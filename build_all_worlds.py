#!/usr/bin/env python3
"""
Build multiple worlds for MythOS demo
"""
import sys
import json
from pathlib import Path

# Add the services directory to the path
sys.path.append('services/island_scorer')

from build import build_island

def build_all_worlds():
    """Build all demo worlds"""
    worlds = [
        {
            "world_id": "greek_myth",
            "corpus_path": "corpus/greek_myth",
            "description": "Ancient Greek mythology and epic literature"
        },
        {
            "world_id": "fantasy_realm", 
            "corpus_path": "corpus/fantasy_realm",
            "description": "High fantasy with elves, dragons, and magic"
        },
        {
            "world_id": "vampire_cyberpunk",
            "corpus_path": "corpus/vampire_cyberpunk", 
            "description": "Cyberpunk future with vampires and technology"
        }
    ]
    
    for world in worlds:
        print(f"\n🏗️ Building world: {world['world_id']}")
        print(f"   Description: {world['description']}")
        print(f"   Corpus: {world['corpus_path']}")
        
        try:
            # Check if corpus exists
            corpus_path = Path(world['corpus_path'])
            if not corpus_path.exists():
                print(f"   ❌ Corpus directory not found: {corpus_path}")
                continue
                
            # Get list of text files
            txt_files = list(corpus_path.glob("*.txt"))
            if not txt_files:
                print(f"   ❌ No .txt files found in {corpus_path}")
                continue
                
            print(f"   📚 Found {len(txt_files)} text files")
            
            # Build the island (it will look for corpus_dir/world_id/*.txt)
            meta = build_island(
                world_id=world['world_id'],
                corpus_dir="corpus",  # Base directory - function will add world_id
                model_id="sentence-transformers/all-MiniLM-L6-v2"
            )
            
            print(f"   ✅ World built successfully!")
            print(f"   📊 Chunks: {meta['num_chunks']}")
            print(f"   🎯 Accept threshold: {meta['T_accept']:.4f}")
            print(f"   ⚠️  Review threshold: {meta['T_review']:.4f}")
            
        except Exception as e:
            print(f"   ❌ Failed to build {world['world_id']}: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("🏛️ MythOS Multi-World Builder")
    print("=" * 40)
    build_all_worlds()
    print("\n🎉 All worlds processed!")
    print("\nYou can now test different genres in the demo:")
    print("• Greek Mythology - Ancient gods and heroes")  
    print("• Fantasy Realm - Elves, dragons, and magic")
    print("• Vampire Cyberpunk - Digital bloodsuckers and neon nights")
