"""
MythOS Editor - Live Worldliness Meter + Neighbors
Week 3: Complete integration of Island Scorer + Prose Store
"""
import asyncio
import json
import time
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from pydantic import BaseModel, Field
import requests
import aiohttp


app = FastAPI(
    title="MythOS Editor",
    description="Live worldliness meter and semantic neighbors for immersive writing",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files - adjust path for running from root directory
app.mount("/static", StaticFiles(directory="services/editor/static"), name="static")

# Service URLs
ISLAND_SCORER_URL = "http://localhost:8000"
PROSE_STORE_URL = "http://localhost:8001"

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()


# Pydantic models
class EditorRequest(BaseModel):
    world_id: str = Field(..., description="World identifier")
    text: str = Field(..., description="Current text being written")
    cursor_position: int = Field(default=0, description="Current cursor position")
    context_window: int = Field(default=200, description="Characters around cursor for analysis")

class LiveMeterResponse(BaseModel):
    world_id: str
    iw_score: float
    decision: str  # ACCEPT/REVIEW/REJECT
    confidence: float
    nearest_chunks: List[str]
    distances: List[float]
    prose_neighbors: List[Dict[str, Any]]
    world_stats: Dict[str, Any]
    suggestions: List[str]

class WorldConnection(BaseModel):
    world_id: str = Field(..., description="World to connect to")
    initialize_corpus: bool = Field(default=True, description="Build island if not exists")

class DocumentSaveRequest(BaseModel):
    world_id: str
    title: str
    content: str
    author: Optional[str] = None
    auto_validate: bool = Field(default=True, description="Run through Island Scorer")


class EditorService:
    """Core service for integrating Island Scorer and Prose Store"""
    
    def __init__(self):
        self.session = None
    
    async def get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None
    
    async def check_services(self):
        """Verify both services are available"""
        session = await self.get_session()
        
        try:
            # Check Island Scorer
            async with session.get(f"{ISLAND_SCORER_URL}/health") as resp:
                island_health = await resp.json()
            
            # Check Prose Store
            async with session.get(f"{PROSE_STORE_URL}/health") as resp:
                prose_health = await resp.json()
            
            return {
                "island_scorer": island_health,
                "prose_store": prose_health,
                "integration_ready": True
            }
        except Exception as e:
            return {
                "island_scorer": {"status": "unreachable"},
                "prose_store": {"status": "unreachable"},
                "integration_ready": False,
                "error": str(e)
            }
    
    async def get_live_score(self, world_id: str, text: str):
        """Get real-time worldliness score from Island Scorer"""
        session = await self.get_session()
        
        try:
            payload = {"world_id": world_id, "text": text}
            async with session.post(f"{ISLAND_SCORER_URL}/score", json=payload) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    raise HTTPException(status_code=resp.status, detail=error_text)
        except aiohttp.ClientError as e:
            raise HTTPException(status_code=503, detail=f"Island Scorer unavailable: {str(e)}")
    
    async def get_prose_neighbors(self, world_id: str, text: str, limit: int = 5):
        """Get semantically similar prose from Prose Store"""
        session = await self.get_session()
        
        try:
            # Extract key terms for search
            search_terms = self._extract_search_terms(text)
            
            params = {"q": search_terms, "world_id": world_id, "limit": limit}
            async with session.get(f"{PROSE_STORE_URL}/search", params=params) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get("spans", [])
                else:
                    return []
        except aiohttp.ClientError:
            return []
    
    async def get_world_stats(self, world_id: str):
        """Get world statistics from Prose Store"""
        session = await self.get_session()
        
        try:
            async with session.get(f"{PROSE_STORE_URL}/worlds/{world_id}/stats") as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return {"error": "World not found in Prose Store"}
        except aiohttp.ClientError:
            return {"error": "Prose Store unavailable"}
    
    async def save_document(self, world_id: str, title: str, content: str, author: str = None):
        """Save document to Prose Store"""
        session = await self.get_session()
        
        try:
            payload = {
                "world_id": world_id,
                "title": title,
                "content": content,
                "author": author,
                "metadata": {"created_via": "mythos_editor", "timestamp": time.time()}
            }
            
            async with session.post(f"{PROSE_STORE_URL}/documents", json=payload) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    raise HTTPException(status_code=resp.status, detail=error_text)
        except aiohttp.ClientError as e:
            raise HTTPException(status_code=503, detail=f"Prose Store unavailable: {str(e)}")
    
    async def validate_document(self, world_id: str, content: str):
        """Validate entire document through Island Scorer"""
        session = await self.get_session()
        
        try:
            # Split into paragraphs for validation
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            results = []
            
            for para in paragraphs:
                payload = {"world_id": world_id, "text": para}
                async with session.post(f"{ISLAND_SCORER_URL}/score", json=payload) as resp:
                    if resp.status == 200:
                        score_result = await resp.json()
                        results.append({
                            "text": para[:80] + "..." if len(para) > 80 else para,
                            "iw_score": score_result["iw_score"],
                            "decision": score_result["decision"]
                        })
            
            # Calculate overall validation
            avg_score = sum(r["iw_score"] for r in results) / len(results) if results else 0
            reject_count = sum(1 for r in results if r["decision"] == "REJECT")
            
            return {
                "overall_score": avg_score,
                "paragraph_results": results,
                "reject_count": reject_count,
                "recommendation": "ACCEPT" if reject_count == 0 and avg_score > 0.3 else "REVIEW" if reject_count < 2 else "REJECT"
            }
        except aiohttp.ClientError as e:
            raise HTTPException(status_code=503, detail=f"Validation failed: {str(e)}")
    
    def _extract_search_terms(self, text: str) -> str:
        """Extract meaningful terms for prose search"""
        # Simple keyword extraction - could be enhanced with NLP
        words = text.split()
        # Filter out common words and focus on content words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        meaningful_words = [w for w in words if len(w) > 3 and w.lower() not in stop_words]
        return " ".join(meaningful_words[:5])  # Top 5 meaningful words
    
    def _generate_suggestions(self, iw_score: float, decision: str, nearest_chunks: List[str]) -> List[str]:
        """Generate writing suggestions based on score and context"""
        suggestions = []
        
        if decision == "REJECT":
            suggestions.append("Consider using more world-appropriate terminology")
            suggestions.append("This content seems out of place for this world")
            if nearest_chunks:
                suggestions.append(f"Try incorporating elements like: {nearest_chunks[0][:50]}...")
        
        elif decision == "REVIEW":
            suggestions.append("Good direction, but could be more world-specific")
            if iw_score < 0.4:
                suggestions.append("Add more mythological or world-specific details")
            if nearest_chunks:
                suggestions.append(f"Consider similar phrasing to: {nearest_chunks[0][:50]}...")
        
        else:  # ACCEPT
            suggestions.append("Excellent! This fits well with the world")
            suggestions.append("Your writing matches the established tone")
        
        return suggestions

# Global service instance
editor_service = EditorService()


# API Endpoints

@app.get("/")
async def serve_editor():
    """Redirect to the main editor interface"""
    return RedirectResponse(url="/static/index.html")

@app.get("/health")
async def health_check():
    """Health check including service dependencies"""
    service_status = await editor_service.check_services()
    return {
        "status": "healthy",
        "service": "mythos_editor",
        "dependencies": service_status
    }

@app.post("/connect", response_model=Dict[str, Any])
async def connect_to_world(request: WorldConnection):
    """Connect to a world and initialize if needed"""
    world_id = request.world_id
    
    # Check if world exists in Island Scorer
    try:
        session = await editor_service.get_session()
        async with session.get(f"{ISLAND_SCORER_URL}/world/{world_id}/status") as resp:
            if resp.status == 404 and request.initialize_corpus:
                # Try to build the world from corpus
                build_payload = {
                    "world_id": world_id,
                    "corpus_path": f"corpus/{world_id.replace('-', '_')}",
                    "chunk_size": 200,
                    "overlap": 50
                }
                
                async with session.post(f"{ISLAND_SCORER_URL}/build", json=build_payload) as build_resp:
                    if build_resp.status == 200:
                        build_result = await build_resp.json()
                    else:
                        raise HTTPException(status_code=400, detail="Failed to build world island")
            elif resp.status == 200:
                build_result = await resp.json()
            else:
                raise HTTPException(status_code=404, detail="World not found and corpus unavailable")
    except aiohttp.ClientError:
        raise HTTPException(status_code=503, detail="Island Scorer unavailable")
    
    # Get world stats from Prose Store
    world_stats = await editor_service.get_world_stats(world_id)
    
    return {
        "world_id": world_id,
        "connected": True,
        "island_scorer_status": build_result,
        "prose_store_stats": world_stats,
        "ready_for_editing": True
    }

@app.post("/live-meter", response_model=LiveMeterResponse)
async def get_live_meter(request: EditorRequest):
    """Get real-time worldliness analysis"""
    try:
        world_id = request.world_id
        
        # Extract context around cursor for analysis
        text = request.text
        cursor_pos = request.cursor_position
        context_window = request.context_window
        
        # Get context window around cursor
        start_pos = max(0, cursor_pos - context_window // 2)
        end_pos = min(len(text), cursor_pos + context_window // 2)
        context_text = text[start_pos:end_pos].strip()
        
        if not context_text:
            # Use entire text if context is empty
            context_text = text.strip()
        
        if not context_text:
            raise HTTPException(status_code=400, detail="No text to analyze")
        
        # Get Island Scorer analysis
        score_result = await editor_service.get_live_score(world_id, context_text)
        
        # Get prose neighbors from Prose Store
        prose_neighbors = await editor_service.get_prose_neighbors(world_id, context_text)
        
        # Get world stats
        world_stats = await editor_service.get_world_stats(world_id)
        
        # Generate suggestions
        suggestions = editor_service._generate_suggestions(
            score_result["iw_score"],
            score_result["decision"],
            score_result.get("nearest_chunks", [])
        )
        
        return LiveMeterResponse(
            world_id=world_id,
            iw_score=score_result["iw_score"],
            decision=score_result["decision"],
            confidence=score_result["confidence"],
            nearest_chunks=score_result.get("nearest_chunks", []),
            distances=score_result.get("distances", []),
            prose_neighbors=prose_neighbors,
            world_stats=world_stats,
            suggestions=suggestions
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Live meter error: {str(e)}")

@app.post("/save-document")
async def save_document(request: DocumentSaveRequest):
    """Save document with optional validation"""
    # Save to Prose Store
    doc_result = await editor_service.save_document(
        request.world_id,
        request.title,
        request.content,
        request.author
    )
    
    # Optional validation through Island Scorer
    validation_result = None
    if request.auto_validate:
        validation_result = await editor_service.validate_document(
            request.world_id,
            request.content
        )
    
    return {
        "document": doc_result,
        "validation": validation_result,
        "saved_at": time.time()
    }

@app.websocket("/ws/{world_id}")
async def websocket_endpoint(websocket: WebSocket, world_id: str):
    """WebSocket for real-time editing feedback"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive text updates from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "text_update":
                # Get live analysis
                try:
                    request = EditorRequest(
                        world_id=world_id,
                        text=message["text"],
                        cursor_position=message.get("cursor_position", 0),
                        context_window=message.get("context_window", 200)
                    )
                    
                    # Get live meter response
                    if request.text.strip():
                        meter_response = await get_live_meter(request)
                        
                        # Send analysis back to client
                        await manager.send_personal_message(
                            json.dumps({
                                "type": "live_analysis",
                                "data": meter_response.dict()
                            }),
                            websocket
                        )
                    
                except Exception as e:
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "error",
                            "message": str(e)
                        }),
                        websocket
                    )
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/worlds")
async def list_available_worlds():
    """List available worlds across both services"""
    try:
        session = await editor_service.get_session()
        
        # Get worlds from Prose Store
        async with session.get(f"{PROSE_STORE_URL}/documents") as resp:
            if resp.status == 200:
                docs = await resp.json()
                prose_worlds = list(set(doc.get("world_id") for doc in docs if doc.get("world_id")))
            else:
                prose_worlds = []
        
        # Check which have Island Scorer support
        world_status = {}
        for world in prose_worlds:
            try:
                async with session.get(f"{ISLAND_SCORER_URL}/world/{world}/status") as resp:
                    if resp.status == 200:
                        status = await resp.json()
                        world_status[world] = {
                            "prose_store": True,
                            "island_scorer": True,
                            "chunks": status.get("total_chunks", 0)
                        }
                    else:
                        world_status[world] = {
                            "prose_store": True,
                            "island_scorer": False,
                            "chunks": 0
                        }
            except:
                world_status[world] = {
                    "prose_store": True,
                    "island_scorer": False,
                    "chunks": 0
                }
        
        return {
            "available_worlds": world_status,
            "integration_status": "ready"
        }
    
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to list worlds: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    await editor_service.close_session()


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8002))
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )
