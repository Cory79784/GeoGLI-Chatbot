"""
LangGraph state machine for routing queries between Route A (Structured) and Route B (RAG)
Currently configured to route all queries to Route B (RAG)
"""
from typing import Dict, Any
from langgraph.graph import Graph
from app.schemas import GraphState
from app.rag.retriever import dense_retriever
from app.llm.provider import llm_provider
import time


def start_node(state: GraphState) -> GraphState:
    """Initialize the graph state"""
    print(f"Starting query processing for session: {state['session_id']}")
    return state


def parse_query(state: GraphState) -> GraphState:
    """
    Parse the user query to extract structured information
    This is a simple implementation - can be enhanced with NLP parsing
    """
    message = state["message"].lower()
    
    # Simple keyword-based parsing
    parsed = {}
    
    # Extract potential location mentions
    location_keywords = ["country", "region", "area", "location", "place"]
    if any(keyword in message for keyword in location_keywords):
        parsed["has_location"] = True
    
    # Extract potential time mentions  
    time_keywords = ["year", "period", "time", "recent", "latest", "historical"]
    if any(keyword in message for keyword in time_keywords):
        parsed["has_time"] = True
    
    # Extract potential indicator mentions
    indicator_keywords = ["indicator", "degradation", "productivity", "carbon", "vegetation"]
    if any(keyword in message for keyword in indicator_keywords):
        parsed["has_indicator"] = True
    
    state["parsed"] = parsed
    print(f"Parsed query: {parsed}")
    
    return state


def router(state: GraphState) -> GraphState:
    """
    Route queries between Route A (Structured) and Route B (RAG)
    
    Current logic: Always route to Route B
    Future enhancement: Use parsed information to determine routing
    """
    # For MVP: Always use Route B (RAG)
    state["route"] = "B"
    
    # TODO: Implement intelligent routing based on parsed query
    # Example future logic:
    # if (state["parsed"].get("has_location") and 
    #     state["parsed"].get("has_indicator") and
    #     state["route_hint"] != "B"):
    #     state["route"] = "A"
    # else:
    #     state["route"] = "B"
    
    print(f"Routed to: Route {state['route']}")
    return state


# Route A implementation - FULLY COMMENTED
# To enable Route A:
# 1. Uncomment the function below
# 2. Uncomment connector imports at the top of this file  
# 3. Update router() function to conditionally route to "A"
# 4. Add Route A to the graph edges

# def run_route_a(state: GraphState) -> GraphState:
#     """
#     Route A: Structured queries using PostGIS, Elasticsearch, and OGC services
#     
#     This route handles spatial and structured queries that can be answered
#     with direct database/service queries rather than RAG retrieval.
#     """
#     from app.connectors.postgis import postgis_connector
#     from app.connectors.elastic import elasticsearch_connector  
#     from app.connectors.ogc import ogc_connector
    
#     message = state["message"]
#     parsed = state["parsed"]
    
#     try:
#         results = []
        
#         # Example: Spatial query using PostGIS
#         if parsed.get("has_location") and parsed.get("has_indicator"):
#             # This would need actual location parsing to extract WKT geometry
#             # For now, this is a placeholder showing the structure
#             spatial_results = postgis_connector.query_by_location(
#                 location_wkt="POINT(-74.0059 40.7128)",  # Example: NYC coordinates
#                 start_year=2010,
#                 end_year=2023
#             )
#             results.extend(spatial_results)
        
#         # Example: Keyword search using Elasticsearch
#         if not results:
#             search_results = elasticsearch_connector.keyword_search(
#                 query_text=message,
#                 size=10
#             )
#             results.extend(search_results)
        
#         # Format results
#         if results:
#             # Convert structured results to answer format
#             answer_parts = []
#             source_links = []
            
#             for result in results[:5]:  # Limit to top 5 results
#                 if "indicator_name" in result:
#                     answer_parts.append(f"{result['indicator_name']}: {result.get('value', 'N/A')}")
#                 if "source_url" in result:
#                     source_links.append(result["source_url"])
            
#             state["answer"] = "\n".join(answer_parts) if answer_parts else "No structured data found."
#             state["source_links"] = source_links
#             state["citations"] = [{"source": r.get("source", "Unknown")} for r in results]
#         else:
#             state["route"] = "cannot_answer"
#             state["reason"] = "No structured data sources available"
    
#     except Exception as e:
#         print(f"Route A error: {e}")
#         state["route"] = "cannot_answer" 
#         state["reason"] = f"Route A processing error: {str(e)}"
    
#     return state


def run_route_b(state: GraphState) -> GraphState:
    """
    Route B: RAG-based queries using vector similarity search
    
    This is the main route for the MVP, handling general questions
    about land indicators using document retrieval and LLM generation.
    """
    message = state["message"]
    
    try:
        # Retrieve relevant documents
        top_k = 6  # TODO: PERFORMANCE - make configurable
        retrieved_docs = dense_retriever.retrieve(message, top_k)
        
        if not retrieved_docs:
            state["route"] = "cannot_answer"
            state["reason"] = "No relevant documents found in knowledge base"
            return state
        
        # Check retrieval confidence (simple threshold-based)
        # TODO: PERFORMANCE - tune confidence threshold
        min_score = 0.3
        high_confidence_docs = [doc for doc in retrieved_docs if doc.get("score", 0) > min_score]
        
        if not high_confidence_docs:
            state["route"] = "cannot_answer"
            state["reason"] = "Retrieved documents have low confidence scores"
            return state
        
        # Generate answer using LLM
        answer = llm_provider.generate(high_confidence_docs, message)
        
        # Extract source links
        source_links = []
        citations = []
        
        for doc in high_confidence_docs:
            source = doc.get("source", "")
            if source:
                # Create source link (URL or doc#page format)
                if source.startswith("http"):
                    source_links.append(source)
                else:
                    # Local document reference
                    page = doc.get("chunk_id", 0)
                    source_links.append(f"{source}#page{page}")
                
                citations.append({
                    "source": source,
                    "page": doc.get("chunk_id"),
                    "score": doc.get("score")
                })
        
        state["answer"] = answer
        state["source_links"] = list(set(source_links))  # Remove duplicates
        state["citations"] = citations
        
    except Exception as e:
        print(f"Route B error: {e}")
        state["route"] = "cannot_answer"
        state["reason"] = f"RAG processing error: {str(e)}"
    
    return state


def handle_cannot_answer(state: GraphState) -> GraphState:
    """Handle queries that cannot be answered confidently"""
    reason = state.get("reason", "Insufficient information")
    
    # Generate helpful cannot_answer response
    state["answer"] = (
        "I can't answer confidently with current sources. "
        "Please provide more specific information about location, time, or indicator. "
        f"(Reason: {reason})"
    )
    state["source_links"] = []
    state["citations"] = []
    
    return state


def format_output(state: GraphState) -> GraphState:
    """Format the final output"""
    # Ensure all required fields are present
    if not state.get("answer"):
        state["answer"] = "No answer generated"
    
    if not state.get("source_links"):
        state["source_links"] = []
    
    if not state.get("citations"):
        state["citations"] = []
    
    print(f"Final route: {state['route']}")
    print(f"Answer length: {len(state['answer'])} characters")
    print(f"Sources: {len(state['source_links'])}")
    
    return state


def create_graph() -> Graph:
    """Create and configure the LangGraph workflow"""
    
    # Define the graph
    graph = Graph()
    
    # Add nodes
    graph.add_node("start", start_node)
    graph.add_node("parse_query", parse_query)
    graph.add_node("router", router)
    # graph.add_node("route_a", run_route_a)  # Commented - Route A disabled
    graph.add_node("route_b", run_route_b)
    graph.add_node("cannot_answer", handle_cannot_answer)
    graph.add_node("format_output", format_output)
    
    # Define edges
    graph.add_edge("start", "parse_query")
    graph.add_edge("parse_query", "router")
    
    # Router edges - currently only routes to B or cannot_answer
    def route_condition(state: GraphState) -> str:
        route = state.get("route", "B")
        if route == "A":
            # return "route_a"  # Commented - Route A disabled
            return "route_b"  # Fallback to Route B
        elif route == "cannot_answer":
            return "cannot_answer"
        else:
            return "route_b"
    
    graph.add_conditional_edges(
        "router",
        route_condition,
        {
            # "route_a": "route_a",  # Commented - Route A disabled
            "route_b": "route_b",
            "cannot_answer": "cannot_answer"
        }
    )
    
    # All routes lead to format_output
    # graph.add_edge("route_a", "format_output")  # Commented - Route A disabled
    graph.add_edge("route_b", "format_output")
    graph.add_edge("cannot_answer", "format_output")
    
    # Set entry and exit points
    graph.set_entry_point("start")
    graph.set_finish_point("format_output")
    
    return graph.compile()

