"""
Pydantic v2 models for the GeoGLI chatbot
"""
from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class QueryRequest(BaseModel):
    """Request model for non-streaming query endpoint"""
    q: str = Field(..., max_length=4000, description="User query message")
    session_id: Optional[str] = Field(None, description="Session identifier")
    route_hint: Optional[Literal["A", "B", "auto"]] = Field("auto", description="Routing hint")
    top_k: Optional[int] = Field(None, description="Number of documents to retrieve")


class QueryResponse(BaseModel):
    """Response model for query endpoints"""
    session_id: str
    answer: str
    source_links: List[str]
    route: Literal["A", "B", "cannot_answer"]
    latency_ms: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "ok"


class ErrorResponse(BaseModel):
    """Error response model"""
    msg: str


# LangGraph State - using TypedDict for LangGraph compatibility
class GraphState(TypedDict):
    """State object passed through the LangGraph workflow"""
    session_id: str
    message: str
    route: Literal["A", "B", "auto", "cannot_answer"]
    parsed: Dict  # {location?, time?, indicator?}
    answer: str
    citations: List[Dict]  # [{source, page?}]
    source_links: List[str]
    reason: Optional[str]


# SSE Event models
class TokenEvent(BaseModel):
    """Streaming token event"""
    t: str  # token text


class FinalEvent(BaseModel):
    """Final response event"""
    session_id: str
    answer: str
    source_links: List[str]
    route: Literal["A", "B", "cannot_answer"]
    latency_ms: int


class ErrorEvent(BaseModel):
    """Error event"""
    msg: str


# BM25 Search models
class BM25Hit(BaseModel):
    """BM25 search result hit"""
    title: Optional[str] = None
    text: Optional[str] = None
    section: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    images: Optional[List[str]] = None
    citation_path: Optional[str] = None
    url: Optional[str] = None
    source_csv: Optional[str] = None
    updated_at: Optional[str] = None
    score: Optional[float] = Field(default=None, alias="_score")
    intent: Optional[str] = None
    placeholder: Optional[bool] = None


class BM25Response(BaseModel):
    """BM25 search response"""
    intent: str
    hits: List[BM25Hit]
    query: Optional[str] = None
