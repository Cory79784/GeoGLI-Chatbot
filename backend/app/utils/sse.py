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
    Create SSE stream for query processing
    
    This is the main streaming function that will be called by the endpoint.
    It yields SSE-formatted events for token streaming and final response.
    """
    from app.router_graph import create_graph, GraphState
    import time
    
    start_time = time.time()
    
    try:
        # Initialize graph state
        initial_state: GraphState = {
            "session_id": session_id,
            "message": message,
            "route": route_hint,
            "parsed": {},
            "answer": "",
            "citations": [],
            "source_links": [],
            "reason": None
        }
        
        # Create and run the graph
        graph = create_graph()
        
        # For now, we'll simulate streaming by running the graph
        # and then streaming the response token by token
        final_state = graph.invoke(initial_state)
        
        # Stream the answer token by token
        answer = final_state.get("answer", "")
        tokens = answer.split()
        
        for token in tokens:
            yield format_event("token", {"t": token + " "})
        
        # Send final event
        latency_ms = int((time.time() - start_time) * 1000)
        final_data = {
            "session_id": final_state["session_id"],
            "answer": final_state["answer"],
            "source_links": final_state["source_links"],
            "route": final_state["route"],
            "latency_ms": latency_ms
        }
        
        yield format_event("final", final_data)
        
    except Exception as e:
        yield format_event("error", {"msg": str(e)})


def get_sse_headers() -> Dict[str, str]:
    """Get standard SSE response headers"""
    return {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
    }

