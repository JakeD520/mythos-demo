#!/usr/bin/env python3
"""
Test script for Island Scorer API
"""
import requests
import json


def test_island_scorer():
    """Test the Island Scorer API endpoints"""
    
    base_url = "http://127.0.0.1:8001"
    
    print("🏝️  Testing Island Scorer API")
    print("=" * 50)
    
    # Test root endpoint
    print("\n1. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Root: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Root failed: {e}")
    
    # Test health endpoint
    print("\n2. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health failed: {e}")
    
    # Test world status
    print("\n3. Testing world status...")
    try:
        response = requests.get(f"{base_url}/world/greek_myth/status")
        print(f"✅ World Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"❌ World status failed: {e}")
    
    # Test scoring - ACCEPT case
    print("\n4. Testing scoring - Should ACCEPT...")
    try:
        payload = {
            "world_id": "greek_myth",
            "text": "Zeus the mighty thunderer ruled from Olympus with his divine power"
        }
        response = requests.post(f"{base_url}/score", json=payload)
        print(f"✅ Score: {response.status_code}")
        result = response.json()
        print(f"   Status: {result['status']}")
        print(f"   Distance: {result['distance']:.4f}")
        print(f"   IW Score: {result['iw_score']:.4f}")
        print(f"   Top neighbor: {result['neighbors'][0]['source']}")
    except Exception as e:
        print(f"❌ Scoring failed: {e}")
    
    # Test scoring - REVIEW case
    print("\n5. Testing scoring - Should REVIEW...")
    try:
        payload = {
            "world_id": "greek_myth", 
            "text": "The bronze mirror reflected her beauty in the lamplight"
        }
        response = requests.post(f"{base_url}/score", json=payload)
        result = response.json()
        print(f"✅ Score: {response.status_code}")
        print(f"   Status: {result['status']}")
        print(f"   Distance: {result['distance']:.4f}")
        print(f"   IW Score: {result['iw_score']:.4f}")
    except Exception as e:
        print(f"❌ Scoring failed: {e}")
    
    # Test scoring - REJECT case
    print("\n6. Testing scoring - Should REJECT...")
    try:
        payload = {
            "world_id": "greek_myth",
            "text": "Orpheus ignited his lightsaber and fought the storm troopers"
        }
        response = requests.post(f"{base_url}/score", json=payload)
        result = response.json()
        print(f"✅ Score: {response.status_code}")
        print(f"   Status: {result['status']}")
        print(f"   Distance: {result['distance']:.4f}")
        print(f"   IW Score: {result['iw_score']:.4f}")
    except Exception as e:
        print(f"❌ Scoring failed: {e}")
    
    # Test list worlds
    print("\n7. Testing list worlds...")
    try:
        response = requests.get(f"{base_url}/worlds")
        print(f"✅ List Worlds: {response.status_code}")
        worlds = response.json()['worlds']
        print(f"   Found {len(worlds)} world(s)")
        for world in worlds:
            print(f"   - {world['world_id']}: {world['num_chunks']} chunks")
    except Exception as e:
        print(f"❌ List worlds failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Island Scorer testing complete!")


if __name__ == "__main__":
    test_island_scorer()
