#!/usr/bin/env python3
"""
Simple manual test for Island Scorer
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.island_scorer.score import IslandScorer

def test_scorer():
    """Test the scorer directly without API"""
    print("🏝️  Testing Island Scorer Directly")
    print("=" * 40)
    
    try:
        # Initialize scorer
        scorer = IslandScorer(artifacts_dir="artifacts")
        
        # Test world status
        print("\n1. Testing world status...")
        status = scorer.get_world_status("greek_myth")
        print(f"✅ World exists: {status['exists']}")
        if status['exists']:
            print(f"   Chunks: {status['num_chunks']}")
            print(f"   Model: {status['model_id']}")
            print(f"   T_accept: {status['T_accept']:.4f}")
            print(f"   T_review: {status['T_review']:.4f}")
        
        # Test scoring
        test_texts = [
            ("Zeus ruled from Olympus", "ACCEPT candidate"),
            ("The bronze mirror reflected", "REVIEW candidate"), 
            ("Lightsaber battle in space", "REJECT candidate")
        ]
        
        for i, (text, desc) in enumerate(test_texts, 2):
            print(f"\n{i}. Testing: {desc}")
            result = scorer.score_text("greek_myth", text)
            print(f"   Text: {text}")
            print(f"   Status: {result['status']}")
            print(f"   Distance: {result['distance']:.4f}")
            print(f"   IW Score: {result['iw_score']:.4f}")
            print(f"   Top neighbor: {result['neighbors'][0]['source']}")
        
        print("\n" + "=" * 40)
        print("🎉 Direct scorer test complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scorer()
