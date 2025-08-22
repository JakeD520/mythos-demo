#!/usr/bin/env python3
"""
Test script to debug the Editor live meter functionality
"""
import asyncio
import aiohttp
import sys
import json
from pathlib import Path

# Add the current directory to the path
sys.path.append('.')

from services.editor.app import EditorService

async def test_editor_service():
    """Test the EditorService directly"""
    print("🧪 Testing EditorService Live Meter...")
    
    service = EditorService()
    
    try:
        # Test 1: Check services availability
        print("\n1. Checking service availability...")
        status = await service.check_services()
        print(f"   Service status: {json.dumps(status, indent=2)}")
        
        if not status.get("integration_ready"):
            print("❌ Services not ready for integration")
            return False
        
        # Test 2: Test live scoring
        print("\n2. Testing live scoring...")
        world_id = "greek_myth"
        test_text = "Zeus threw thunderbolts from Mount Olympus."
        
        score_result = await service.get_live_score(world_id, test_text)
        print(f"   Score result: {json.dumps(score_result, indent=2)[:500]}...")
        
        # Test 3: Test prose neighbors
        print("\n3. Testing prose neighbors...")
        neighbors = await service.get_prose_neighbors(world_id, test_text)
        print(f"   Found {len(neighbors)} neighbors")
        
        # Test 4: Test world stats
        print("\n4. Testing world stats...")
        stats = await service.get_world_stats(world_id)
        print(f"   World stats: {json.dumps(stats, indent=2)}")
        
        print("\n✅ All EditorService tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ EditorService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await service.close_session()

async def test_direct_api():
    """Test the live meter API endpoint directly"""
    print("\n🌐 Testing Live Meter API endpoint...")
    
    url = "http://localhost:8002/live-meter"
    payload = {
        "world_id": "greek_myth",
        "text": "Zeus threw thunderbolts from Mount Olympus.",
        "cursor_position": 20,
        "context_window": 200
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print(f"✅ Live meter response: {json.dumps(result, indent=2)[:500]}...")
                    return True
                else:
                    error_text = await resp.text()
                    print(f"❌ Live meter failed ({resp.status}): {error_text}")
                    return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🏛️ MythOS Editor Live Meter Test Suite")
    print("=" * 50)
    
    # Test the service layer
    service_ok = await test_editor_service()
    
    if service_ok:
        # Test the API layer
        api_ok = await test_direct_api()
        
        if api_ok:
            print("\n🎉 All tests passed! Live meter should be working.")
        else:
            print("\n⚠️  Service layer works but API layer fails.")
    else:
        print("\n❌ Service layer failed - check service connections.")

if __name__ == "__main__":
    asyncio.run(main())
