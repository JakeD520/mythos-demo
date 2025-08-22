"""
FastAPI app for Island Scorer service
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import traceback
from pathlib import Path

from services.island_scorer.models import (
    BuildRequest, BuildResponse, ScoreRequest, ScoreResponse, 
    WorldStatus, ErrorResponse
)
from services.island_scorer.build import build_island
from services.island_scorer.score import IslandScorer


# Initialize FastAPI app
app = FastAPI(
    title="Island Scorer",
    description="Vector-first prose world coherence gating",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize scorer
artifacts_dir = os.getenv("ARTIFACTS_DIR", "artifacts")
corpus_dir = os.getenv("CORPUS_DIR", "corpus")
scorer = IslandScorer(artifacts_dir=artifacts_dir)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Island Scorer",
        "version": "1.0.0",
        "description": "Vector-first prose world coherence gating"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/build", response_model=BuildResponse)
async def build_world_island(request: BuildRequest):
    """
    Build island artifacts for a world
    """
    try:
        meta = build_island(
            world_id=request.world_id,
            corpus_dir=corpus_dir,
            artifacts_dir=artifacts_dir,
            model_id=request.model_id,
            target_words=request.target_words,
            overlap_words=request.overlap_words,
            k=request.k,
            accept_q=request.accept_q,
            review_q=request.review_q,
            sources=request.sources
        )
        
        # Clear cache for this world since we rebuilt it
        scorer.clear_cache(request.world_id)
        
        return BuildResponse(
            success=True,
            world_id=meta['world_id'],
            manifold_version=meta['manifold_version'],
            num_chunks=meta['num_chunks'],
            dim=meta['dim'],
            T_accept=meta['T_accept'],
            T_review=meta['T_review'],
            model_id=meta['model_id'],
            message=f"Island built successfully with {meta['num_chunks']} chunks"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Build failed: {str(e)}"
        )


@app.post("/score", response_model=ScoreResponse)
async def score_text(request: ScoreRequest):
    """
    Score text against world island
    """
    try:
        result = scorer.score_text(request.world_id, request.text)
        
        return ScoreResponse(**result)
        
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scoring failed: {str(e)}"
        )


@app.get("/world/{world_id}/status", response_model=WorldStatus)
async def get_world_status(world_id: str):
    """
    Get status information for a world
    """
    try:
        status = scorer.get_world_status(world_id)
        return WorldStatus(**status)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get world status: {str(e)}"
        )


@app.delete("/world/{world_id}/cache")
async def clear_world_cache(world_id: str):
    """
    Clear cached data for a world
    """
    try:
        scorer.clear_cache(world_id)
        return {"message": f"Cache cleared for world '{world_id}'"}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )


@app.get("/worlds")
async def list_worlds():
    """
    List available worlds
    """
    try:
        artifacts_path = Path(artifacts_dir)
        if not artifacts_path.exists():
            return {"worlds": []}
        
        worlds = []
        for world_dir in artifacts_path.iterdir():
            if world_dir.is_dir():
                status = scorer.get_world_status(world_dir.name)
                worlds.append(status)
        
        return {"worlds": worlds}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list worlds: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
