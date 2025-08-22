"""
Prose Store + Reader Demo
Shows practical usage of the document storage and search system
"""
import requests
import json
import time
from pathlib import Path


class ProseStoreClient:
    """Simple client for interacting with Prose Store API"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
    
    def create_document(self, world_id: str, title: str, content: str, author: str = None, metadata: dict = None):
        """Create a new document"""
        data = {
            "world_id": world_id,
            "title": title,
            "content": content,
            "author": author,
            "metadata": metadata or {}
        }
        response = requests.post(f"{self.base_url}/documents", json=data)
        response.raise_for_status()
        return response.json()
    
    def search(self, query: str, world_id: str = None):
        """Search for text spans"""
        params = {"q": query}
        if world_id:
            params["world_id"] = world_id
        response = requests.get(f"{self.base_url}/search", params=params)
        response.raise_for_status()
        return response.json()
    
    def aggregate_relationships(self, world_id: str, window_size: int = 2):
        """Build relationship graph"""
        data = {"world_id": world_id, "window_size": window_size}
        response = requests.post(f"{self.base_url}/worlds/{world_id}/aggregate", json=data)
        response.raise_for_status()
        return response.json()
    
    def get_edges(self, world_id: str, limit: int = 20):
        """Get relationship edges"""
        response = requests.get(f"{self.base_url}/worlds/{world_id}/edges", params={"limit": limit})
        response.raise_for_status()
        return response.json()
    
    def get_stats(self, world_id: str):
        """Get world statistics"""
        response = requests.get(f"{self.base_url}/worlds/{world_id}/stats")
        response.raise_for_status()
        return response.json()


def demo_mythological_world():
    """Demo using mythological content"""
    print("🏛️  Creating Mythological World Demo")
    print("=" * 50)
    
    client = ProseStoreClient()
    world_id = "mythology-demo"
    
    # Create sample documents
    documents = [
        {
            "title": "The Birth of Athena",
            "author": "Ancient Chronicle",
            "content": """Zeus, the mighty ruler of Olympus, suffered from terrible headaches that shook the very foundations of heaven. The cause was his unborn daughter, Athena, growing within his skull after he had swallowed her mother Metis.

Unable to bear the pain any longer, Zeus called upon Hephaestus, the god of fire and forge. With his mighty hammer and chisel, Hephaestus struck Zeus's head with tremendous force.

From the crack in Zeus's skull emerged Athena, fully grown and clad in gleaming armor. She sprang forth with a war cry that echoed across the heavens, causing all the gods to marvel at her wisdom and beauty.

Athena became the goddess of wisdom, warfare, and crafts, beloved by mortals for her fair judgment and protection of heroes."""
        },
        {
            "title": "Perseus and Medusa",
            "author": "Hero's Chronicle", 
            "content": """Perseus, son of Zeus and the mortal princess Danae, was tasked with an impossible quest: to bring back the head of Medusa, the gorgon whose gaze could turn any living creature to stone.

Armed with gifts from the gods - Athena's polished shield, Hermes' winged sandals, and Hades' helm of invisibility - Perseus embarked on his perilous journey to the edge of the world.

Using Athena's shield as a mirror to avoid Medusa's deadly gaze, Perseus carefully approached the sleeping gorgon. With one swift stroke of his divine sword, he severed her head.

From Medusa's blood sprang forth Pegasus, the winged horse, and Chrysaor, the golden warrior. Perseus used Medusa's head as a powerful weapon in his subsequent adventures."""
        },
        {
            "title": "Theseus and the Minotaur",
            "author": "Athenian Records",
            "content": """King Minos of Crete demanded a terrible tribute from Athens: seven young men and seven young women to be fed to the Minotaur, a creature half-man and half-bull that dwelt in an impossible labyrinth.

Theseus, prince of Athens, volunteered to be among the tribute, secretly planning to slay the monster and end the cruel practice. His father, King Aegeus, wept as the black-sailed ship departed for Crete.

Princess Ariadne, daughter of King Minos, fell in love with the brave Theseus. She provided him with a ball of thread to navigate the labyrinth and a sword to defeat the Minotaur.

Following Ariadne's thread through the twisting passages, Theseus found the beast and fought it in deadly combat. After slaying the Minotaur, he followed the thread back to freedom, escaping with Ariadne and the other Athenians."""
        }
    ]
    
    print("📚 Creating mythological documents...")
    for doc in documents:
        result = client.create_document(
            world_id=world_id,
            title=doc["title"],
            author=doc["author"],
            content=doc["content"],
            metadata={"genre": "mythology", "culture": "greek"}
        )
        print(f"✅ Created: {doc['title']} (ID: {result['id'][:8]}...)")
    
    # Let documents process
    time.sleep(1)
    
    # Build relationship graph
    print(f"\n🔗 Building relationship graph...")
    agg_result = client.aggregate_relationships(world_id, window_size=2)
    print(f"✅ {agg_result['message']}")
    
    # Search for various terms
    print(f"\n🔍 Searching mythological content...")
    search_terms = [
        "Zeus",
        "Athena wisdom", 
        "Medusa gorgon",
        "labyrinth Minotaur",
        "sword combat",
        "gods divine"
    ]
    
    for term in search_terms:
        results = client.search(term, world_id=world_id)
        print(f"🔎 '{term}': {len(results['spans'])} results")
        if results['spans']:
            best_match = results['spans'][0]
            print(f"   📖 {best_match['text'][:80]}...")
    
    # Show relationship edges
    print(f"\n🌐 Top relationships in {world_id}:")
    edges = client.get_edges(world_id, limit=10)
    for i, edge in enumerate(edges[:5], 1):
        print(f"{i}. Weight {edge['weight']:.1f}: {edge['source_text'][:40]}... → {edge['target_text'][:40]}...")
    
    # Show world statistics
    print(f"\n📊 World Statistics:")
    stats = client.get_stats(world_id)
    for key, value in stats.items():
        if key != "world_id":
            print(f"   {key.replace('_', ' ').title()}: {value}")
    
    return world_id


def demo_search_capabilities(world_id: str):
    """Demonstrate advanced search capabilities"""
    print(f"\n🔍 Advanced Search Demo for {world_id}")
    print("=" * 50)
    
    client = ProseStoreClient()
    
    # Test various search patterns
    searches = [
        ("hero", "Generic term"),
        ("Zeus Athena", "Multiple names"),
        ("divine sword", "Items and attributes"),
        ("labyrinth impossible", "Complex descriptors"),
        ("princess love", "Emotional content"),
        ("combat deadly", "Action sequences")
    ]
    
    for query, description in searches:
        print(f"\n🎯 Testing: {description}")
        print(f"   Query: '{query}'")
        
        results = client.search(query, world_id=world_id)
        print(f"   Results: {len(results['spans'])} spans found")
        
        # Show top 2 results
        for i, span in enumerate(results['spans'][:2], 1):
            print(f"   {i}. {span['text'][:100]}...")


def demo_real_time_updates():
    """Demonstrate real-time document updates and versioning"""
    print(f"\n🔄 Real-time Updates Demo")
    print("=" * 30)
    
    client = ProseStoreClient()
    world_id = "updates-demo"
    
    # Create initial document
    initial_content = """The Oracle's Prophecy speaks of a chosen hero who will rise in the darkest hour. This hero shall wield the power of the ancient gods and restore balance to the realm."""
    
    doc = client.create_document(
        world_id=world_id,
        title="The Oracle's Prophecy",
        author="Seer Pythia",
        content=initial_content,
        metadata={"status": "draft", "version": "1.0"}
    )
    
    print(f"📖 Created prophecy document: {doc['id'][:8]}...")
    
    # Search for initial content
    results = client.search("chosen hero", world_id=world_id)
    print(f"🔍 Initial search for 'chosen hero': {len(results['spans'])} results")
    
    # TODO: Add document update functionality
    # This would require implementing PUT /documents/{id} endpoint
    print("📝 Document versioning and updates ready for implementation")
    
    return world_id


def main():
    """Run the complete demo"""
    print("🏺 PROSE STORE + READER DEMO")
    print("🔥 Week 2 of MythOS Timeline")
    print("=" * 60)
    
    try:
        # Check if service is running
        response = requests.get("http://localhost:8001/health")
        print(f"✅ Prose Store service is running: {response.json()}")
        
        # Run demos
        mythology_world = demo_mythological_world()
        demo_search_capabilities(mythology_world)
        demo_real_time_updates()
        
        print("\n" + "=" * 60)
        print("🎉 DEMO COMPLETE!")
        print("🏛️  The Prose Store + Reader is fully operational")
        print("📚 Ready for integration with Island Scorer")
        print("🚀 Week 2 milestone achieved!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Prose Store service")
        print("💡 Start the service with: python app.py")
        print("   Or: uvicorn app:app --host 0.0.0.0 --port 8001")
    
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
