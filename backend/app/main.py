"""
FastAPI main application for UNCCD GeoGLI chatbot
Provides health check and streaming query endpoints
"""
import os
import time
from typing import Optional
from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.schemas import HealthResponse, QueryResponse, ErrorResponse
from app.utils.ids import get_session_id_from_request
from app.utils.sse import create_sse_stream, get_sse_headers
from app.routes import export
from app.database import db

# Load environment variables
load_dotenv()

# BM25 configuration
RAG_BM25_ENABLED = os.getenv("RAG_BM25_ENABLED", "true").lower() == "true"

# Dense RAG configuration (disabled for MVP)
RAG_DENSE_ENABLED = os.getenv("RAG_DENSE_ENABLED", "false").lower() == "true"

# Create FastAPI app
app = FastAPI(
    title="UNCCD GeoGLI Chatbot",
    description="Minimal chatbot for UNCCD Global Land Indicator queries",
    version="1.0.0"
)

# Configure CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Initialize BM25 stores if enabled
if RAG_BM25_ENABLED:
    try:
        from app.search.bm25_store import build_all_stores
        app.state.bm25_stores = build_all_stores()
        print(f"✅ BM25 stores initialized: {list(app.state.bm25_stores.keys())}")
    except Exception as e:
        print(f"⚠️  Failed to initialize BM25 stores: {e}")
        app.state.bm25_stores = {}
else:
    app.state.bm25_stores = {}
    print("ℹ️  BM25 search disabled (RAG_BM25_ENABLED=false)")

# Store dense RAG configuration
app.state.rag_dense_enabled = RAG_DENSE_ENABLED
print(f"ℹ️  Dense RAG: {'enabled' if RAG_DENSE_ENABLED else 'disabled (BM25 only)'}")

# Serve static data files (snapshots, citations)
# Files under backend/data/ are exposed at /static-data/
# Mount static files for BM25 images and citations
# Try different possible data directory locations
possible_data_dirs = [
    os.path.join(os.path.dirname(__file__), "..", "data"),  # backend/data (relative to this file)
    os.path.join(os.getcwd(), "backend", "data"),           # from project root
    os.path.join(os.getcwd(), "data")                       # from backend dir
]

DATA_DIR = None
for data_dir in possible_data_dirs:
    abs_path = os.path.abspath(data_dir)
    if os.path.isdir(abs_path):
        DATA_DIR = abs_path
        break

if DATA_DIR:
    app.mount("/static-data", StaticFiles(directory=DATA_DIR), name="static-data")
    print(f"📁 Static data served from {DATA_DIR} at /static-data/")
else:
    print(f"ℹ️  Data directory not found. Tried: {possible_data_dirs}")

# Include routers
app.include_router(export.router)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="ok")


@app.get("/query/stream")
async def stream_query(
    request: Request,
    q: str = Query(..., max_length=4000, description="User query message"),
    session_id: Optional[str] = Query(None, description="Session identifier"),
    route_hint: Optional[str] = Query("auto", regex="^(A|B|auto)$", description="Routing hint"),
    top_k: Optional[int] = Query(None, ge=1, le=20, description="Number of documents to retrieve")
):
    """
    Streaming query endpoint using Server-Sent Events (SSE)
    
    Returns:
        text/event-stream with token and final events
    """
    try:
        # Get or generate session ID
        header_session_id = request.headers.get("X-Session-Id")
        final_session_id = get_session_id_from_request(session_id, header_session_id)
        
        # Set default top_k if not provided
        if top_k is None:
            top_k = int(os.getenv("TOP_K", "6"))
        
        # Create SSE stream
        stream = create_sse_stream(
            session_id=final_session_id,
            message=q,
            route_hint=route_hint,
            top_k=top_k
        )
        
        # Create streaming response with proper headers
        headers = get_sse_headers()
        headers["X-Session-Id"] = final_session_id
        
        return StreamingResponse(
            stream,
            media_type="text/event-stream",
            headers=headers
        )
        
    except Exception as e:
        # Return error as JSON for non-streaming errors
        raise HTTPException(status_code=500, detail=str(e))


from pydantic import BaseModel

class QueryBody(BaseModel):
    q: str | None = None
    query: str | None = None
    text: str | None = None
    route_hint: str | None = None
    session_id: str | None = None
    top_k: int | None = None

async def _handle_query_common(request: Request, q: str | None, route_hint: str | None, session_id: str | None):
    """Internal unified handler for both GET and POST /query"""
    # Accept JSON body too
    body = {}
    if request.headers.get("content-type","").startswith("application/json"):
        try:
            body = await request.json()
        except Exception:
            body = {}

    # Prefer URL q; fallback to JSON body fields
    q = q or body.get("q") or body.get("query") or body.get("text")
    route_hint = route_hint or body.get("route_hint", "auto")
    session_id = session_id or body.get("session_id")

    if not q:
        return JSONResponse({"detail": "q required"}, status_code=422)

    # Set safe default for BM25 search
    top_k = int(os.getenv("BM25_TOP_K", "3"))

    try:
        from app.router_graph import create_graph
        from app.schemas import GraphState
        
        # Get or generate session ID
        header_session_id = request.headers.get("X-Session-Id")
        final_session_id = get_session_id_from_request(session_id, header_session_id)
        
        # Set default top_k if not provided
        if top_k is None:
            top_k = int(os.getenv("TOP_K", "6"))
        
        # Validate input length
        if len(q) > 4000:
            raise HTTPException(status_code=413, detail="Query too long (max 4000 characters)")
        
        # Process query
        start_time = time.time()
        
        initial_state: GraphState = {
            "session_id": final_session_id,
            "message": q,
            "route": route_hint,
            "parsed": {},
            "answer": "",
            "citations": [],
            "source_links": [],
            "reason": None
        }
        
        # --- BM25 PRE-CHECK (before LangGraph) ---
        # Check for BM25 hits first to avoid LangGraph processing
        if RAG_BM25_ENABLED and hasattr(app.state, 'bm25_stores') and app.state.bm25_stores:
            try:
                from app.search.router_intent import route as route_intent
                from app.search.handlers import (
                    handle_ask_country, handle_commit_region, 
                    handle_commit_country, handle_law_lookup,
                    format_hits_for_response
                )
                
                # Route the query to get intent and slots
                slots = route_intent(q)
                intent = slots.get("intent", "ask.country")
                hits = []
                
                # Handle different intents
                if intent == "ask.country":
                    hits = handle_ask_country(q, slots, app.state.bm25_stores)
                elif intent == "commit.region":
                    hits = handle_commit_region(q, slots, app.state.bm25_stores)
                elif intent == "commit.country":
                    hits = handle_commit_country(q, slots, app.state.bm25_stores)
                elif intent == "law.lookup":
                    hits = handle_law_lookup(q, slots, app.state.bm25_stores)
                
                # If we got BM25 hits, return immediately without LangGraph
                if hits:
                    print(f"BM25 hit for intent '{intent}' - bypassing LangGraph completely")
                    
                    # Map local file paths to served URLs
                    def to_public_path(p):
                        if isinstance(p, str) and p.startswith("backend/data"):
                            return p.replace("backend/data", "/static-data")
                        return p
                    
                    for hit in hits:
                        if "images" in hit and isinstance(hit["images"], list):
                            hit["images"] = [to_public_path(x) for x in hit["images"]]
                        if "citation_path" in hit and isinstance(hit["citation_path"], str):
                            hit["citation_path"] = to_public_path(hit["citation_path"])
                    
                    # Format hits and return structured response
                    formatted_hits = format_hits_for_response(hits, intent)
                    
                    # Calculate latency
                    latency_ms = int((time.time() - start_time) * 1000)
                    
                    # Return BM25 structured response directly
                    bm25_response = {
                        "intent": intent,
                        "hits": formatted_hits,
                        "query": q,
                        "session_id": final_session_id,
                        "latency_ms": latency_ms
                    }
                    
                    json_response = JSONResponse(content=bm25_response)
                    json_response.headers["X-Session-Id"] = final_session_id
                    return json_response
                    
            except Exception as bm25_error:
                print(f"BM25 pre-check error: {bm25_error}")
                # Fall through to LangGraph
        
        # --- END BM25 PRE-CHECK ---
        
        # Run the graph (only if BM25 didn't return results)
        graph = create_graph()
        final_state = graph.invoke(initial_state)
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Check if this was a BM25 response that should return structured data
        if (final_state.get("route") == "BM25" and 
            "bm25_response" in final_state and 
            RAG_BM25_ENABLED):
            # Return BM25 structured response instead of regular QueryResponse
            bm25_data = final_state["bm25_response"]
            bm25_data["latency_ms"] = latency_ms
            bm25_data["session_id"] = final_state["session_id"]
            
            json_response = JSONResponse(content=bm25_data)
            json_response.headers["X-Session-Id"] = final_state["session_id"]
            return json_response
        
        # Regular response for RAG/other routes
        response = QueryResponse(
            session_id=final_state["session_id"],
            answer=final_state["answer"],
            source_links=final_state["source_links"],
            route=final_state["route"],
            latency_ms=latency_ms
        )
        
        # Add session ID to response headers
        json_response = JSONResponse(content=response.dict())
        json_response.headers["X-Session-Id"] = final_session_id
        
        return json_response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/query")
async def query_get(
    request: Request,
    q: str | None = Query(default=None),
    route_hint: str | None = Query(default=None),
    session_id: str | None = Query(default=None),
):
    return await _handle_query_common(request, q, route_hint, session_id)


@app.post("/query")
async def query_post(
    request: Request,
    q: str | None = Query(default=None),
    route_hint: str | None = Query(default=None),
    session_id: str | None = Query(default=None),
):
    return await _handle_query_common(request, q, route_hint, session_id)

@app.get("/debug/bm25")
async def debug_bm25(q: str = Query(..., description="Query to test BM25 search")):
    """Debug endpoint to quickly verify BM25 hits"""
    if not RAG_BM25_ENABLED or not hasattr(app.state, 'bm25_stores'):
        return {"error": "BM25 not enabled or stores not available"}
    
    try:
        from app.search.router_intent import route as route_intent
        from app.search.handlers import handle_ask_country
        
        stores = app.state.bm25_stores
        slots = route_intent(q)
        intent = slots.get("intent", "ask.country")
        
        # For debug, just test geogli store
        hits = handle_ask_country(q, slots, stores)
        
        return {
            "query": q,
            "intent": intent, 
            "slots": slots,
            "hits_count": len(hits),
            "hits": hits[:3],  # Show first 3 hits
            "available_stores": list(stores.keys())
        }
    except Exception as e:
        return {"error": str(e)}


@app.exception_handler(413)
async def request_entity_too_large_handler(request: Request, exc: HTTPException):
    """Handle request entity too large errors"""
    return JSONResponse(
        status_code=413,
        content=ErrorResponse(msg="Request too large").dict()
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: HTTPException):
    """Handle internal server errors"""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(msg="Internal server error").dict()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
