"""
Test script for Prose Store + Reader
"""
import asyncio
import json
from pathlib import Path
import sys

# Add the prose_store directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from db import ProseDB


def test_basic_operations():
    """Test basic database operations"""
    print("🧪 Testing basic database operations...")
    
    # Initialize database
    db = ProseDB(db_path="test_prose.db")
    
    # Test document creation
    print("\n📖 Creating test document...")
    doc_id, version = db.create_document(
        doc_id="test-doc-1",
        world_id="test-world",
        content="""The ancient city of Athenia stood majestically atop the crystalline cliffs overlooking the Sapphire Sea. Its white marble towers gleamed in the eternal twilight, casting long shadows across the terraced gardens where luminescent flowers bloomed.

In the heart of the city, the Great Library housed scrolls of forgotten wisdom. Scholars from distant realms traveled here to study the mysteries of the cosmos, seeking answers to questions that had puzzled civilizations for millennia.

The High Priestess Lyanna walked through the marble corridors, her silver robes rustling softly. She carried an ancient tome bound in dragonhide, its pages filled with prophecies that spoke of a coming convergence of worlds.""",
        title="The Chronicles of Athenia",
        author="Sage Elianor",
        metadata={"genre": "fantasy", "year": 2024}
    )
    
    print(f"✅ Created document: {doc_id}, version: {version}")
    
    # Test document retrieval
    print("\n📚 Retrieving document...")
    document = db.get_document(doc_id)
    print(f"✅ Retrieved: {document['title']} by {document['author']}")
    print(f"   📊 Words: {document['word_count']}, Characters: {document['char_count']}")
    
    # Test span creation
    print("\n📝 Creating spans...")
    spans_data = [
        {
            "start_pos": 0,
            "end_pos": 267,
            "text": "The ancient city of Athenia stood majestically atop the crystalline cliffs overlooking the Sapphire Sea. Its white marble towers gleamed in the eternal twilight, casting long shadows across the terraced gardens where luminescent flowers bloomed.",
            "span_type": "paragraph",
            "metadata": {"paragraph_number": 1}
        },
        {
            "start_pos": 269,
            "end_pos": 490,
            "text": "In the heart of the city, the Great Library housed scrolls of forgotten wisdom. Scholars from distant realms traveled here to study the mysteries of the cosmos, seeking answers to questions that had puzzled civilizations for millennia.",
            "span_type": "paragraph",
            "metadata": {"paragraph_number": 2}
        },
        {
            "start_pos": 492,
            "end_pos": 719,
            "text": "The High Priestess Lyanna walked through the marble corridors, her silver robes rustling softly. She carried an ancient tome bound in dragonhide, its pages filled with prophecies that spoke of a coming convergence of worlds.",
            "span_type": "paragraph",
            "metadata": {"paragraph_number": 3}
        }
    ]
    
    span_ids = db.create_spans(doc_id, version, "test-world", spans_data)
    print(f"✅ Created {len(span_ids)} spans: {span_ids}")
    
    # Test span retrieval
    print("\n🔍 Retrieving spans...")
    spans = db.get_spans(doc_id)
    for span in spans:
        print(f"   📝 Span {span['id']}: {span['text'][:50]}...")
    
    # Test full-text search
    print("\n🔎 Testing full-text search...")
    search_results = db.search_spans("ancient wisdom", world_id="test-world")
    print(f"✅ Found {len(search_results)} results for 'ancient wisdom':")
    for result in search_results:
        print(f"   🎯 {result['text'][:80]}...")
    
    # Test search for specific terms
    print("\n🔍 Searching for 'Lyanna'...")
    lyanna_results = db.search_spans("Lyanna", world_id="test-world")
    print(f"✅ Found {len(lyanna_results)} results for 'Lyanna':")
    for result in lyanna_results:
        print(f"   👤 {result['text'][:80]}...")
    
    # Test edge creation and aggregation
    print("\n🔗 Testing relationship aggregation...")
    db.aggregate_window("test-world", window_size=2)
    edges = db.get_top_edges("test-world", limit=10)
    print(f"✅ Created {len(edges)} edges:")
    for edge in edges[:3]:  # Show top 3
        print(f"   🔗 Weight {edge['weight']:.2f}: {edge['source_text'][:30]}... → {edge['target_text'][:30]}...")
    
    # Test document listing
    print("\n📋 Testing document listing...")
    docs = db.list_documents(world_id="test-world")
    print(f"✅ Found {len(docs)} documents in test-world:")
    for doc in docs:
        print(f"   📄 {doc['title']} ({doc['word_count']} words)")
    
    print("\n🎉 All basic operations completed successfully!")
    return True


async def test_api_operations():
    """Test API operations with FastAPI client"""
    print("\n🌐 Testing API operations...")
    
    # Import FastAPI test client
    from fastapi.testclient import TestClient
    from app import app
    
    client = TestClient(app)
    
    # Test health check
    print("\n❤️ Testing health check...")
    response = client.get("/health")
    assert response.status_code == 200
    print(f"✅ Health check: {response.json()}")
    
    # Test document creation via API
    print("\n📖 Creating document via API...")
    doc_data = {
        "world_id": "api-test-world",
        "title": "The Digital Grimoire",
        "author": "Code Wizard",
        "content": """Welcome to the digital realm where bytes flow like rivers of light through silicon valleys. Here, algorithms dance in harmony with data structures, creating symphonies of computation.

The great servers hum with ancient knowledge, their memory banks storing the collective wisdom of countless programmers. Each function call echoes through the virtual halls like incantations of power.

In this realm, bugs are the dark creatures that lurk in the shadows of poorly written code, waiting to corrupt the perfect harmony of logical execution. Only the skilled debugger can banish them back to the void.""",
        "metadata": {"genre": "tech-fantasy", "platform": "digital"}
    }
    
    response = client.post("/documents", json=doc_data)
    assert response.status_code == 200
    created_doc = response.json()
    print(f"✅ Created document: {created_doc['id']}")
    
    # Test document retrieval
    print("\n📚 Retrieving document via API...")
    response = client.get(f"/documents/{created_doc['id']}")
    assert response.status_code == 200
    retrieved_doc = response.json()
    print(f"✅ Retrieved: {retrieved_doc['title']}")
    
    # Test span retrieval
    print("\n📝 Retrieving spans via API...")
    response = client.get(f"/documents/{created_doc['id']}/spans")
    assert response.status_code == 200
    spans = response.json()
    print(f"✅ Found {len(spans)} spans")
    
    # Test search
    print("\n🔎 Testing search via API...")
    response = client.get("/search", params={"q": "algorithms", "world_id": "api-test-world"})
    assert response.status_code == 200
    search_results = response.json()
    print(f"✅ Search found {len(search_results['spans'])} spans for 'algorithms'")
    
    # Test aggregation
    print("\n🔗 Testing aggregation via API...")
    agg_data = {"world_id": "api-test-world", "window_size": 1}
    response = client.post("/worlds/api-test-world/aggregate", json=agg_data)
    assert response.status_code == 200
    print(f"✅ Aggregation completed: {response.json()['message']}")
    
    # Test edge retrieval
    print("\n🌐 Testing edge retrieval via API...")
    response = client.get("/worlds/api-test-world/edges")
    assert response.status_code == 200
    edges = response.json()
    print(f"✅ Found {len(edges)} edges")
    
    # Test world stats
    print("\n📊 Testing world stats via API...")
    response = client.get("/worlds/api-test-world/stats")
    assert response.status_code == 200
    stats = response.json()
    print(f"✅ World stats: {stats['document_count']} docs, {stats['span_count']} spans, {stats['edge_count']} edges")
    
    print("\n🎉 All API operations completed successfully!")
    return True


def test_advanced_search():
    """Test advanced search capabilities"""
    print("\n🔍 Testing advanced search capabilities...")
    
    db = ProseDB(db_path="test_prose.db")
    
    # Create a more complex document for testing
    complex_content = """The Academy of Mystical Arts was founded in the year 847 of the Third Age by the renowned sorceress Morgana Starweaver. Located on the floating island of Aethermoor, it serves as the premier institution for magical education in the known realms.

Students arrive at the Academy through various means - some by flying carpets, others by teleportation circles, and a few brave souls attempt the treacherous climb up the anchor chains that tether the island to the mountain below.

The curriculum includes fundamental courses such as Basic Incantations, Elemental Manipulation, and Theoretical Thaumaturgy. Advanced students may specialize in areas like Battle Magic, Healing Arts, or the forbidden school of Necromancy.

Professor Aldric Moonwhisper, the current Headmaster, has served the Academy for over two centuries. His vast knowledge of ancient magics and patient teaching style have made him beloved by generations of students.

The Great Library houses over ten thousand magical tomes, scrolls, and artifacts. The most dangerous texts are kept in the Restricted Section, protected by both physical locks and powerful ward spells that would turn an unauthorized reader to ash."""
    
    doc_id, version = db.create_document(
        doc_id="academy-chronicle",
        world_id="magical-realm",
        content=complex_content,
        title="Chronicles of the Academy",
        author="Scholar Benedictus",
        metadata={"type": "historical_record", "classification": "public"}
    )
    
    # Auto-generate spans
    import re
    paragraphs = re.split(r'\n\s*\n', complex_content.strip())
    spans_data = []
    current_pos = 0
    
    for i, para in enumerate(paragraphs):
        para = para.strip()
        if para:
            start_pos = complex_content.find(para, current_pos)
            end_pos = start_pos + len(para)
            spans_data.append({
                'start_pos': start_pos,
                'end_pos': end_pos,
                'text': para,
                'span_type': 'paragraph',
                'metadata': {'paragraph_number': i + 1}
            })
            current_pos = end_pos
    
    db.create_spans(doc_id, version, "magical-realm", spans_data)
    
    # Test various search queries
    test_queries = [
        ("Academy", "Should find multiple references"),
        ("Morgana", "Should find the founder reference"),
        ("teleportation", "Should find transportation methods"),
        ("forbidden Necromancy", "Should find complex phrase"),
        ("Professor Moonwhisper", "Should find the headmaster"),
        ("magical tomes", "Should find library contents")
    ]
    
    for query, description in test_queries:
        results = db.search_spans(query, world_id="magical-realm")
        print(f"🔍 '{query}' ({description}): {len(results)} results")
        if results:
            print(f"   🎯 Best match: {results[0]['text'][:80]}...")
    
    # Test aggregation with different window sizes
    print(f"\n🔗 Testing aggregation with different window sizes...")
    for window_size in [1, 2, 3]:
        db.aggregate_window("magical-realm", window_size)
        edges = db.get_top_edges("magical-realm", limit=5)
        print(f"   Window size {window_size}: {len(edges)} edges")
        if edges:
            top_edge = edges[0]
            print(f"     🥇 Top edge (weight {top_edge['weight']:.2f}): {top_edge['source_text'][:30]}... → {top_edge['target_text'][:30]}...")
    
    print("\n🎉 Advanced search testing completed!")
    return True


def cleanup_test_files():
    """Clean up test database files"""
    import gc
    import time
    
    # Force garbage collection to close any open connections
    gc.collect()
    time.sleep(0.1)  # Brief pause
    
    test_files = ["test_prose.db", "prose_store.db"]
    for file in test_files:
        try:
            if Path(file).exists():
                Path(file).unlink()
                print(f"🧹 Cleaned up {file}")
        except PermissionError:
            print(f"⚠️ Could not clean up {file} (file in use)")


if __name__ == "__main__":
    print("🚀 Starting Prose Store + Reader Tests")
    print("=" * 50)
    
    try:
        # Run tests
        test_basic_operations()
        asyncio.run(test_api_operations())
        test_advanced_search()
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED! Prose Store is ready to use.")
        
        # Show final stats
        db = ProseDB(db_path="test_prose.db")
        with db.get_connection() as conn:
            doc_count = conn.execute("SELECT COUNT(*) as count FROM documents").fetchone()['count']
            span_count = conn.execute("SELECT COUNT(*) as count FROM spans").fetchone()['count']
            edge_count = conn.execute("SELECT COUNT(*) as count FROM edges").fetchone()['count']
        
        print(f"\n📊 Test Database Final Stats:")
        print(f"   📄 Documents: {doc_count}")
        print(f"   📝 Spans: {span_count}")
        print(f"   🔗 Edges: {edge_count}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        print(f"\n🧹 Cleaning up test files...")
        cleanup_test_files()
        print("✅ Cleanup complete!")
