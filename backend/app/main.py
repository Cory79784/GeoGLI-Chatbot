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
from dotenv import load_dotenv

from app.schemas import HealthResponse, QueryResponse, ErrorResponse
from app.utils.ids import get_session_id_from_request
from app.utils.sse import create_sse_stream, get_sse_headers

# Load environment variables
load_dotenv()

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


@app.post("/query", response_model=QueryResponse)
async def non_stream_query(
    request: Request,
    q: str,
    session_id: Optional[str] = None,
    route_hint: Optional[str] = "auto",
    top_k: Optional[int] = None
):
    """
    Non-streaming query endpoint (optional implementation)
    Returns the same final JSON as the SSE final event
    """
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
        
        # Run the graph
        graph = create_graph()
        final_state = graph.invoke(initial_state)
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Create response
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
