#!/usr/bin/env python3
"""
Standalone Island Scorer server for testing
"""
import uvicorn
from services.island_scorer.app import app

if __name__ == "__main__":
    print("🏝️  Starting Island Scorer Server...")
    print("   URL: http://127.0.0.1:8001")
    print("   Docs: http://127.0.0.1:8001/docs")
    print("   Press Ctrl+C to stop")
    
    uvicorn.run(
        app, 
        host="127.0.0.1", 
        port=8001,
        log_level="info"
    )
