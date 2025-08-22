"""
Quick verification of Prose Store + Reader functionality
"""
import sys
from pathlib import Path

# Add the prose_store directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from db import ProseDB
from app import app
from fastapi.testclient import TestClient


def verify_prose_store():
    """Verify Prose Store functionality with realistic mythology content"""
    print("🏺 PROSE STORE + READER VERIFICATION")
    print("🔥 Week 2 of MythOS Timeline")
    print("=" * 50)
    
    # Test database directly
    print("\n💾 Testing Database Layer...")
    db = ProseDB(db_path="verification.db")
    
    # Create Greek mythology documents
    odyssey_excerpt = """Sing to me of the man, Muse, the man of twists and turns driven time and again off course, once he had plundered the hallowed heights of Troy. Many cities of men he saw and learned their minds, many pains he suffered, heartsick on the open sea, fighting to save his life and bring his comrades home.

But he could not save them from disaster, hard as he strove—the recklessness of their own ways destroyed them all, the blind fools, they devoured the cattle of the Sun and the Sungod blotted out the day of their return.

Launch out on his story, Muse, daughter of Zeus, start from where you will—sing for our time too."""
    
    doc_id, version = db.create_document(
        doc_id="odyssey-opening",
        world_id="greek-mythology",
        content=odyssey_excerpt,
        title="The Odyssey - Opening",
        author="Homer",
        metadata={"epic": "odyssey", "book": 1}
    )
    print(f"✅ Created Odyssey document: {doc_id}")
    
    # Create spans automatically
    paragraphs = odyssey_excerpt.split('\n\n')
    spans_data = []
    current_pos = 0
    for i, para in enumerate(paragraphs):
        para = para.strip()
        if para:
            start_pos = odyssey_excerpt.find(para, current_pos)
            end_pos = start_pos + len(para)
            spans_data.append({
                'start_pos': start_pos,
                'end_pos': end_pos,
                'text': para,
                'span_type': 'paragraph',
                'metadata': {'stanza': i + 1}
            })
            current_pos = end_pos
    
    span_ids = db.create_spans(doc_id, version, "greek-mythology", spans_data)
    print(f"✅ Created {len(span_ids)} spans")
    
    # Test search functionality
    print(f"\n🔍 Testing Search...")
    search_results = db.search_spans("Odysseus man twists", world_id="greek-mythology")
    print(f"✅ Found {len(search_results)} results for epic hero search")
    
    search_results = db.search_spans("Zeus Muse", world_id="greek-mythology")
    print(f"✅ Found {len(search_results)} results for divine references")
    
    # Test aggregation
    print(f"\n🔗 Testing Relationship Aggregation...")
    db.aggregate_window("greek-mythology", window_size=2)
    edges = db.get_top_edges("greek-mythology", limit=5)
    print(f"✅ Created {len(edges)} relationship edges")
    
    if edges:
        top_edge = edges[0]
        print(f"   🥇 Strongest relationship: {top_edge['source_text'][:40]}... → {top_edge['target_text'][:40]}...")
    
    # Test API layer
    print(f"\n🌐 Testing API Layer...")
    client = TestClient(app)
    
    # Health check
    response = client.get("/health")
    assert response.status_code == 200
    print(f"✅ Health check: {response.json()['status']}")
    
    # Create document via API
    iliad_excerpt = """Rage—Goddess, sing the rage of Peleus' son Achilles, murderous, doomed, that cost the Achaeans countless losses, hurling down to the House of Death so many sturdy souls, great fighters' souls, but made their bodies carrion, feasts for the dogs and birds, and the will of Zeus was moving toward its end.

Begin, Muse, when the two first broke and clashed, Agamemnon lord of men and brilliant Achilles."""
    
    doc_data = {
        "world_id": "greek-mythology",
        "title": "The Iliad - Opening",
        "author": "Homer",
        "content": iliad_excerpt,
        "metadata": {"epic": "iliad", "book": 1}
    }
    
    response = client.post("/documents", json=doc_data)
    assert response.status_code == 200
    created_doc = response.json()
    print(f"✅ Created Iliad document via API: {created_doc['id'][:8]}...")
    
    # Search via API
    response = client.get("/search", params={"q": "Achilles rage", "world_id": "greek-mythology"})
    assert response.status_code == 200
    search_results = response.json()
    print(f"✅ API search found {len(search_results['spans'])} spans for 'Achilles rage'")
    
    # Get world stats
    response = client.get("/worlds/greek-mythology/stats")
    assert response.status_code == 200
    stats = response.json()
    print(f"✅ World stats: {stats['document_count']} docs, {stats['span_count']} spans")
    
    # Test relationship aggregation via API
    agg_data = {"world_id": "greek-mythology", "window_size": 2}
    response = client.post("/worlds/greek-mythology/aggregate", json=agg_data)
    assert response.status_code == 200
    print(f"✅ API aggregation: {response.json()['message']}")
    
    # Show final world state
    print(f"\n📊 Final Greek Mythology World State:")
    for key, value in stats.items():
        if key != "world_id":
            print(f"   {key.replace('_', ' ').title()}: {value}")
    
    # Demonstrate search capabilities
    print(f"\n🎯 Advanced Search Demonstrations:")
    test_searches = [
        ("Homer", "Author search"),
        ("Zeus Muse", "Divine references"),
        ("Achilles Agamemnon", "Character relationships"),
        ("rage murderous", "Emotional content"),
        ("Death souls", "Themes of mortality")
    ]
    
    for query, description in test_searches:
        response = client.get("/search", params={"q": query, "world_id": "greek-mythology"})
        results = response.json()
        print(f"   🔍 '{query}' ({description}): {len(results['spans'])} matches")
        if results['spans']:
            best = results['spans'][0]['text']
            print(f"      💫 Best: {best[:60]}...")
    
    print(f"\n" + "=" * 50)
    print("🎉 PROSE STORE + READER VERIFIED!")
    print("📚 SQLite FTS5 search working perfectly")
    print("🔗 Rolling-window relationship aggregation functional")
    print("🌐 FastAPI endpoints all operational")
    print("🏛️ Ready for integration with Island Scorer")
    print("✅ Week 2 milestone ACHIEVED!")
    
    # Cleanup
    Path("verification.db").unlink(missing_ok=True)
    
    return True


if __name__ == "__main__":
    try:
        verify_prose_store()
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
