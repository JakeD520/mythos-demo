#!/usr/bin/env python3
"""
Quick API test for Island Scorer
"""
import time
import requests
import json
import threading
import uvicorn
from services.island_scorer.app import app

def start_server():
    """Start the server in a thread"""
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="warning")

def test_api():
    """Test the API endpoints"""
    # Wait for server to start
    time.sleep(2)
    
    base_url = "http://127.0.0.1:8001"
    
    print("🏝️  Testing Island Scorer API")
    print("=" * 40)
    
    try:
        # Test health
        print("\n1. Testing health...")
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Health: {response.status_code} - {response.json()}")
        
        # Test world status
        print("\n2. Testing world status...")
        response = requests.get(f"{base_url}/world/greek_myth/status", timeout=5)
        status = response.json()
        print(f"✅ World Status: {response.status_code}")
        print(f"   Exists: {status['exists']}")
        print(f"   Chunks: {status['num_chunks']}")
        
        # Test scoring
        print("\n3. Testing scoring...")
        payload = {
            "world_id": "greek_myth",
            "text": "Zeus the mighty thunderer ruled from Olympus"
        }
        response = requests.post(f"{base_url}/score", json=payload, timeout=10)
        result = response.json()
        print(f"✅ Score: {response.status_code}")
        print(f"   Status: {result['status']}")
        print(f"   Distance: {result['distance']:.4f}")
        print(f"   IW Score: {result['iw_score']:.4f}")
        
        print("\n" + "=" * 40)
        print("🎉 API test successful!")
        
    except Exception as e:
        print(f"❌ API test failed: {e}")

if __name__ == "__main__":
    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Test the API
    test_api()
