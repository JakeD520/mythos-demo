"""
Pydantic models for Island Scorer API
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class BuildRequest(BaseModel):
    """Request to build island artifacts for a world"""
    world_id: str = Field(..., description="World identifier")
    sources: Optional[List[str]] = Field(None, description="Optional list of source file patterns")
    model_id: Optional[str] = Field("sentence-transformers/all-MiniLM-L6-v2", description="Embedding model to use")
    target_words: Optional[int] = Field(100, description="Target words per chunk")
    overlap_words: Optional[int] = Field(20, description="Overlap words between chunks")
    k: Optional[int] = Field(8, description="Number of nearest neighbors for threshold calculation")
    accept_q: Optional[float] = Field(0.95, description="Accept threshold quantile")
    review_q: Optional[float] = Field(0.99, description="Review threshold quantile")


class BuildResponse(BaseModel):
    """Response from island build operation"""
    success: bool
    world_id: str
    manifold_version: int
    num_chunks: int
    dim: int
    T_accept: float
    T_review: float
    model_id: str
    message: str


class ScoreRequest(BaseModel):
    """Request to score text against a world island"""
    world_id: str = Field(..., description="World identifier")
    text: str = Field(..., description="Text to score")


class Neighbor(BaseModel):
    """A nearest neighbor result"""
    span_id: int = Field(..., description="Span identifier")
    source: str = Field(..., description="Source file name")
    text: str = Field(..., description="Span text content")
    distance: float = Field(..., description="Distance to query")


class ScoreResponse(BaseModel):
    """Response from scoring operation"""
    world_id: str
    text: str
    distance: float = Field(..., description="Average kNN distance to canon")
    iw_score: float = Field(..., description="Island within score (0-1, higher is more in-world)")
    status: str = Field(..., description="ACCEPT, REVIEW, or REJECT")
    neighbors: List[Neighbor] = Field(..., description="Nearest neighbors from canon")
    thresholds: Dict[str, float] = Field(..., description="Decision thresholds")
    manifold_version: int = Field(..., description="Version of the manifold used")
    model_id: str = Field(..., description="Embedding model used")


class WorldStatus(BaseModel):
    """Status information for a world"""
    world_id: str
    exists: bool
    manifold_version: Optional[int] = None
    num_chunks: Optional[int] = None
    model_id: Optional[str] = None
    created_at: Optional[str] = None
    T_accept: Optional[float] = None
    T_review: Optional[float] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    details: Optional[str] = None
