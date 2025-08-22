"""
Prose Store + Reader - FastAPI service for document storage and full-text search
"""
import os
import re
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from services.prose_store.db import ProseDB


app = FastAPI(
    title="Prose Store + Reader",
    description="Document storage with SQLite FTS5 and rolling-window relationship aggregation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global database instance
db = ProseDB()


# Pydantic models
class DocumentCreate(BaseModel):
    world_id: str = Field(..., description="World identifier")
    title: Optional[str] = Field(None, description="Document title")
    author: Optional[str] = Field(None, description="Document author")
    content: str = Field(..., description="Document content")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

class DocumentUpdate(BaseModel):
    content: str = Field(..., description="Updated document content")
    summary: Optional[str] = Field(None, description="Summary of changes")

class DocumentResponse(BaseModel):
    id: str
    world_id: str
    title: Optional[str]
    author: Optional[str]
    current_version: int
    word_count: int
    char_count: int
    metadata: Dict[str, Any]
    created_at: float
    updated_at: float

class DocumentWithContent(DocumentResponse):
    content: str
    summary: Optional[str]

class SpanResponse(BaseModel):
    id: int
    doc_id: str
    version: int
    world_id: str
    start_pos: int
    end_pos: int
    text: str
    span_type: str
    metadata: Dict[str, Any]
    created_at: float

class EdgeResponse(BaseModel):
    id: int
    world_id: str
    source_span_id: int
    target_span_id: int
    source_text: str
    source_doc_id: str
    target_text: str
    target_doc_id: str
    edge_type: str
    weight: float
    window_size: int
    last_seen: float
    decay_factor: float
    metadata: Dict[str, Any]
    created_at: float
    updated_at: float

class SearchResponse(BaseModel):
    spans: List[SpanResponse]
    total_count: int

class AggregationRequest(BaseModel):
    world_id: str = Field(..., description="World identifier")
    window_size: int = Field(default=1, description="Rolling window size for co-occurrence")


def split_into_paragraphs(content: str) -> List[Dict[str, Any]]:
    """Split content into paragraph spans"""
    paragraphs = []
    current_pos = 0
    
    # Split by double newlines (paragraph breaks)
    paragraph_texts = re.split(r'\n\s*\n', content.strip())
    
    for para_text in paragraph_texts:
        para_text = para_text.strip()
        if not para_text:
            continue
            
        start_pos = content.find(para_text, current_pos)
        if start_pos == -1:
            start_pos = current_pos
        
        end_pos = start_pos + len(para_text)
        
        paragraphs.append({
            'start_pos': start_pos,
            'end_pos': end_pos,
            'text': para_text,
            'span_type': 'paragraph',
            'metadata': {
                'word_count': len(para_text.split()),
                'char_count': len(para_text)
            }
        })
        
        current_pos = end_pos
    
    return paragraphs


# API Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "prose_store"}

@app.post("/documents", response_model=DocumentWithContent)
async def create_document(doc_request: DocumentCreate):
    """Create a new document with automatic span generation"""
    try:
        # Generate document ID if not provided
        doc_id = str(uuid.uuid4())
        
        # Create document
        doc_id, version = db.create_document(
            doc_id=doc_id,
            world_id=doc_request.world_id,
            content=doc_request.content,
            title=doc_request.title,
            author=doc_request.author,
            metadata=doc_request.metadata
        )
        
        # Generate spans (paragraphs)
        spans_data = split_into_paragraphs(doc_request.content)
        if spans_data:
            db.create_spans(doc_id, version, doc_request.world_id, spans_data)
        
        # Return created document
        document = db.get_document(doc_id, version)
        if not document:
            raise HTTPException(status_code=500, detail="Failed to retrieve created document")
        
        return DocumentWithContent(**document)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")

@app.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    world_id: Optional[str] = Query(None, description="Filter by world ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of documents"),
    offset: int = Query(0, ge=0, description="Number of documents to skip")
):
    """List documents with pagination"""
    try:
        documents = db.list_documents(world_id=world_id, limit=limit, offset=offset)
        return [DocumentResponse(**doc) for doc in documents]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@app.get("/documents/{doc_id}", response_model=DocumentWithContent)
async def get_document(
    doc_id: str,
    version: Optional[int] = Query(None, description="Specific version (default: latest)")
):
    """Get document by ID and version"""
    try:
        document = db.get_document(doc_id, version)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentWithContent(**document)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")

@app.put("/documents/{doc_id}", response_model=DocumentWithContent)
async def update_document(doc_id: str, doc_update: DocumentUpdate):
    """Update document content (creates new version)"""
    try:
        # Get document to check if it exists
        existing_doc = db.get_document(doc_id)
        if not existing_doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Create new version
        new_version = db.update_document(doc_id, doc_update.content, doc_update.summary)
        
        # Generate spans for new version
        spans_data = split_into_paragraphs(doc_update.content)
        if spans_data:
            db.create_spans(doc_id, new_version, existing_doc['world_id'], spans_data)
        
        # Return updated document
        document = db.get_document(doc_id, new_version)
        return DocumentWithContent(**document)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update document: {str(e)}")

@app.get("/documents/{doc_id}/spans", response_model=List[SpanResponse])
async def get_document_spans(
    doc_id: str,
    version: Optional[int] = Query(None, description="Specific version (default: latest)")
):
    """Get spans for a document"""
    try:
        spans = db.get_spans(doc_id, version)
        return [SpanResponse(**span) for span in spans]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get spans: {str(e)}")

@app.get("/search", response_model=SearchResponse)
async def search_spans(
    q: str = Query(..., description="Search query"),
    world_id: Optional[str] = Query(None, description="Filter by world ID"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results")
):
    """Full-text search spans using FTS5"""
    try:
        spans = db.search_spans(q, world_id=world_id, limit=limit)
        return SearchResponse(
            spans=[SpanResponse(**span) for span in spans],
            total_count=len(spans)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/worlds/{world_id}/aggregate")
async def aggregate_world_relationships(
    world_id: str,
    request: AggregationRequest
):
    """Aggregate relationships using rolling window co-occurrence"""
    try:
        # Validate window size
        if request.window_size < 1 or request.window_size > 10:
            raise HTTPException(
                status_code=400, 
                detail="Window size must be between 1 and 10"
            )
        
        # Run aggregation
        db.aggregate_window(world_id, request.window_size)
        
        return {
            "status": "success",
            "world_id": world_id,
            "window_size": request.window_size,
            "message": "Relationship aggregation completed"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Aggregation failed: {str(e)}")

@app.get("/worlds/{world_id}/edges", response_model=List[EdgeResponse])
async def get_world_edges(
    world_id: str,
    limit: int = Query(50, ge=1, le=500, description="Maximum number of edges")
):
    """Get top weighted edges for a world"""
    try:
        edges = db.get_top_edges(world_id, limit)
        return [EdgeResponse(**edge) for edge in edges]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get edges: {str(e)}")

@app.get("/worlds/{world_id}/stats")
async def get_world_stats(world_id: str):
    """Get statistics for a world"""
    try:
        # Count documents
        documents = db.list_documents(world_id=world_id, limit=1000)
        doc_count = len(documents)
        
        # Calculate total words/characters
        total_words = sum(doc.get('word_count', 0) for doc in documents)
        total_chars = sum(doc.get('char_count', 0) for doc in documents)
        
        # Count spans (rough estimate)
        with db.get_connection() as conn:
            span_result = conn.execute(
                "SELECT COUNT(*) as count FROM spans WHERE world_id = ?",
                (world_id,)
            ).fetchone()
            span_count = span_result['count'] if span_result else 0
            
            # Count edges
            edge_result = conn.execute(
                "SELECT COUNT(*) as count FROM edges WHERE world_id = ?",
                (world_id,)
            ).fetchone()
            edge_count = edge_result['count'] if edge_result else 0
        
        return {
            "world_id": world_id,
            "document_count": doc_count,
            "span_count": span_count,
            "edge_count": edge_count,
            "total_words": total_words,
            "total_characters": total_chars
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or default to 8001
    port = int(os.environ.get("PORT", 8001))
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )