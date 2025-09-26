"""
Server-Sent Events (SSE) helpers for streaming responses
"""
import json
from typing import AsyncGenerator, Any, Dict


def format_event(event_type: str, data: Any) -> str:
    """
    Format data as SSE event
    
    Args:
        event_type: Event type (token, final, error)
        data: Data to send (will be JSON serialized)
    
    Returns:
        Formatted SSE event string
    """
    if isinstance(data, dict):
        data_str = json.dumps(data)
    else:
        data_str = str(data)
    
    return f"event: {event_type}\ndata: {data_str}\n\n"


async def create_sse_stream(
    session_id: str,
    message: str,
    route_hint: str = "auto",
    top_k: int = 6
) -> AsyncGenerator[str, None]:
    """
    Create SSE stream for query processing with database storage and real streaming
    
    This is the main streaming function that will be called by the endpoint.
    It yields SSE-formatted events for token streaming and final response.
    """
    from app.database import db
    import time
    import os
    import json
    
    start_time = time.time()
    
    # Save user message to database
    db.save_message(session_id, "user", message)
    
    # --- BM25 PRE-ROUTING for SSE (hard short-circuit) ---
    # This must run FIRST, before any LangGraph or LLM imports
    from app.main import app as app_ref
    from app.search.router_intent import route as route_intent
    from app.search.handlers import (
        handle_ask_country, handle_commit_region, 
        handle_commit_country, handle_law_lookup
    )
    
    def _to_public_path(p: str):
        return p.replace("backend/data", "/static-data") if isinstance(p, str) else p
    
    stores = getattr(app_ref.state, "bm25_stores", None)
    dense_enabled = getattr(app_ref.state, "rag_dense_enabled", False)
    
    if stores:
        slots = route_intent(message)
        intent = slots.get("intent", "ask.country")
        hits = []
        try:
            if intent == "ask.country":
                hits = handle_ask_country(message, slots, stores)
            elif intent == "commit.region":
                hits = handle_commit_region(message, slots, stores)
            elif intent == "commit.country":
                hits = handle_commit_country(message, slots, stores)
            elif intent == "law.lookup":
                hits = handle_law_lookup(message, slots, stores)
        except Exception:
            hits = []
        
        # map local file paths → /static-data
        for h in hits:
            if isinstance(h.get("images"), list):
                h["images"] = [_to_public_path(x) for x in h["images"]]
            if isinstance(h.get("citation_path"), str):
                h["citation_path"] = _to_public_path(h["citation_path"])
        
        if hits:
            # emit single bm25 event then RETURN (do NOT run LangGraph/LLM)
            print(f"✅ BM25 HIT: Found {len(hits)} results - hard short-circuit in SSE")
            yield format_event("bm25", json.dumps({"intent": intent, "hits": hits}))
            # (optional) a final done event
            yield format_event("done", "")
            return
        
        # No hits:
        if not dense_enabled:
            # with dense disabled, return empty hits instead of touching LLM
            print(f"❌ BM25 MISS + Dense disabled - hard short-circuit with empty hits")
            yield format_event("bm25", json.dumps({"intent": intent, "hits": []}))
            yield format_event("done", "")
            return
    # --- END BM25 PRE-ROUTING for SSE ---
    
    # If we reach here, BM25 didn't short-circuit and dense is enabled
    # Import LLM/LangGraph modules only when actually needed
    try:
        from app.router_graph import create_graph, GraphState
        
        # Conditional import for dense retriever
        RAG_DENSE_ENABLED = os.getenv("RAG_DENSE_ENABLED", "false").lower() == "true"
        if RAG_DENSE_ENABLED:
            from app.rag.retriever import dense_retriever
        else:
            dense_retriever = None
        
        # Check if dense RAG is enabled before proceeding
        if not getattr(app.state, "rag_dense_enabled", False):
            print("Dense RAG disabled - returning fallback message")
            fallback_message = "I can only search the available knowledge base. Please try a more specific query about land indicators, commitments, or legislation."
            
            # Save fallback message to database
            db.save_message(session_id, "assistant", fallback_message)
            
            # Return fallback response
            latency_ms = int((time.time() - start_time) * 1000)
            yield format_event("final", {
                "session_id": session_id,
                "answer": fallback_message,
                "source_links": [],
                "route": "BM25_only_fallback",
                "latency_ms": latency_ms
            })
            return
        
        # TODO: Re-enable dense retriever when embedding backend is fixed
        # Check if dense retriever is available
        if dense_retriever is None:
            print("Dense retriever disabled - returning fallback message")
            fallback_message = "I can only search the available knowledge base. Please try a more specific query about land indicators, commitments, or legislation."
            
            # Save fallback message to database
            db.save_message(session_id, "assistant", fallback_message)
            
            # Return fallback response
            latency_ms = int((time.time() - start_time) * 1000)
            yield format_event("final", {
                "session_id": session_id,
                "answer": fallback_message,
                "source_links": [],
                "route": "BM25_only_fallback",
                "latency_ms": latency_ms
            })
            return
        
        # Check if vector index exists before attempting retrieval
        from app.rag.vectorstore import vector_store
        disclaimer = "Note: No matches were found in the internal knowledge base. Answering using general knowledge from the model.\n\n"
        
        # Quick existence check to avoid unnecessary embedding calls
        if not vector_store.exists():
            print("Vector index doesn't exist - falling back to direct LLM")
            # Stream disclaimer first
            full_answer = ""
            for char in disclaimer:
                yield format_event("token", {"t": char})
                full_answer += char
            
            # Then stream direct LLM response
            # Guard LLM import
                RAG_LLM_ENABLED = os.getenv("RAG_LLM_ENABLED", "false").lower() == "true"
                if not RAG_LLM_ENABLED:
                    raise ImportError("LLM disabled")
                from app.llm.provider import stream_generate
            async for token in stream_generate(system_prompt=None, user_prompt=message):
                full_answer += token
                yield format_event("token", {"t": token})
            
            # Save and return
            db.save_message(session_id, "assistant", full_answer)
            yield format_event("final", {
                "session_id": session_id,
                "answer": full_answer,
                "source_links": [],
                "route": "B_fallback",
                "latency_ms": int((time.time() - start_time) * 1000)
            })
            return
        
        # Try document retrieval
        retrieved_docs = dense_retriever.retrieve(message, top_k)
        
        if not retrieved_docs:
            print("No documents retrieved - falling back to direct LLM")
            # Stream disclaimer first
            full_answer = ""
            for char in disclaimer:
                yield format_event("token", {"t": char})
                full_answer += char
            
            # Then stream direct LLM response
            # Guard LLM import
                RAG_LLM_ENABLED = os.getenv("RAG_LLM_ENABLED", "false").lower() == "true"
                if not RAG_LLM_ENABLED:
                    raise ImportError("LLM disabled")
                from app.llm.provider import stream_generate
            async for token in stream_generate(system_prompt=None, user_prompt=message):
                full_answer += token
                yield format_event("token", {"t": token})
            
            # Save and return
            db.save_message(session_id, "assistant", full_answer)
            yield format_event("final", {
                "session_id": session_id,
                "answer": full_answer,
                "source_links": [],
                "route": "B_fallback",
                "latency_ms": int((time.time() - start_time) * 1000)
            })
            return
        
        # Extract source links
        source_links = []
        for doc in retrieved_docs:
            source = doc.get("source", "") or doc.get("meta", {}).get("source", "")
            if source:
                if source.startswith("http"):
                    source_links.append(source)
                else:
                    page = doc.get("chunk_id", 0) or doc.get("meta", {}).get("chunk_id", 0)
                    source_links.append(f"{source}#page{page}")
        source_links = list(set(source_links))  # Remove duplicates
        
        # Check confidence scores for fallback
        min_score = 0.3
        high_confidence_docs = [doc for doc in retrieved_docs if doc.get("score", 0) > min_score]
        
        if not high_confidence_docs:
            print("Low confidence scores - falling back to direct LLM")
            # Stream disclaimer first
            full_answer = ""
            for char in disclaimer:
                yield format_event("token", {"t": char})
                full_answer += char
            
            # Then stream direct LLM response
            # Guard LLM import
                RAG_LLM_ENABLED = os.getenv("RAG_LLM_ENABLED", "false").lower() == "true"
                if not RAG_LLM_ENABLED:
                    raise ImportError("LLM disabled")
                from app.llm.provider import stream_generate
            async for token in stream_generate(system_prompt=None, user_prompt=message):
                full_answer += token
                yield format_event("token", {"t": token})
            
            # Save and return
            db.save_message(session_id, "assistant", full_answer)
            yield format_event("final", {
                "session_id": session_id,
                "answer": full_answer,
                "source_links": [],
                "route": "B_fallback",
                "latency_ms": int((time.time() - start_time) * 1000)
            })
            return
        
        # Stream RAG-based response (normal case)
        print(f"Using RAG with {len(high_confidence_docs)} high-confidence documents")
        full_answer = ""
        # Guard LLM import with feature flag
        RAG_LLM_ENABLED = os.getenv("RAG_LLM_ENABLED", "false").lower() == "true"
        if RAG_LLM_ENABLED:
            try:
                from app.llm.provider import llm_provider
                async for token in llm_provider.generate_stream(high_confidence_docs, message):
                    full_answer += token
                    yield format_event("token", {"t": token})
            except ImportError:
                # LLM provider not available - return document summaries
                summary = f"Found {len(high_confidence_docs)} relevant documents about land indicators."
                for char in summary:
                    yield format_event("token", {"t": char})
                    full_answer += char
        else:
            # LLM disabled - return document summaries
            summary = f"Found {len(high_confidence_docs)} relevant documents about land indicators."
            for char in summary:
                yield format_event("token", {"t": char})
                full_answer += char
        
        # Save assistant response to database
        db.save_message(session_id, "assistant", full_answer)
        
        # Send final event
        latency_ms = int((time.time() - start_time) * 1000)
        final_data = {
            "session_id": session_id,
            "answer": full_answer,
            "source_links": source_links,
            "route": "B",
            "latency_ms": latency_ms
        }
        
        yield format_event("final", final_data)
        
    except Exception as e:
        print(f"Error in RAG processing (falling back to direct LLM): {e}")
        # Fallback to direct LLM even on exceptions
        disclaimer = "Note: No matches were found in the internal knowledge base. Answering using general knowledge from the model.\n\n"
        
        try:
            # Stream disclaimer first
            full_answer = ""
            for char in disclaimer:
                yield format_event("token", {"t": char})
                full_answer += char
            
            # Then stream direct LLM response
            # Guard LLM import
                RAG_LLM_ENABLED = os.getenv("RAG_LLM_ENABLED", "false").lower() == "true"
                if not RAG_LLM_ENABLED:
                    raise ImportError("LLM disabled")
                from app.llm.provider import stream_generate
            async for token in stream_generate(system_prompt=None, user_prompt=message):
                full_answer += token
                yield format_event("token", {"t": token})
            
            # Save and return
            db.save_message(session_id, "assistant", full_answer)
            yield format_event("final", {
                "session_id": session_id,
                "answer": full_answer,
                "source_links": [],
                "route": "B_fallback",
                "latency_ms": int((time.time() - start_time) * 1000)
            })
        except Exception as fallback_error:
            # If even the fallback fails, return error
            error_msg = f"Error processing query: {str(fallback_error)}"
            db.save_message(session_id, "assistant", error_msg)
            yield format_event("error", {"msg": error_msg})


def get_sse_headers() -> Dict[str, str]:
    """Get standard SSE response headers"""
    return {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
    }

