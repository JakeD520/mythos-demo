#!/usr/bin/env python3
"""
Populate Prose Store with mythology content for testing
"""
import requests
import json

PROSE_STORE_URL = "http://localhost:8001"

def add_document(world_id, title, content, author="Homer", metadata=None):
    """Add a document to the Prose Store"""
    payload = {
        "world_id": world_id,
        "title": title,
        "content": content,
        "author": author,
        "metadata": metadata or {}
    }
    
    response = requests.post(f"{PROSE_STORE_URL}/documents", json=payload)
    if response.status_code == 200:
        print(f"✅ Added: {title}")
        return response.json()
    else:
        print(f"❌ Failed to add {title}: {response.status_code} - {response.text}")
        return None

def populate_mythology_world():
    """Add sample mythology content"""
    print("🏛️ Populating Prose Store with Greek mythology content...")
    
    # Document 1: Zeus content
    zeus_content = """Zeus, king of the gods, ruled from Mount Olympus with thunderbolts as his weapons. 
His brothers Poseidon and Hades ruled the seas and underworld respectively. 
Zeus was known for his many love affairs and his children included Athena, Apollo, Artemis, and Hercules.
The mighty god could transform into any shape and his eagle was his sacred animal."""
    
    add_document("greek_myth", "Zeus: King of Olympus", zeus_content, 
                metadata={"deity": "Zeus", "domain": "sky", "type": "mythology"})
    
    # Document 2: Odyssey excerpt
    odyssey_content = """Tell me, Muse, of that man of many ways, who wandered far and wide 
after he had sacked Troy's sacred citadel. Many were the cities whose people he saw and learned their ways,
and many the woes he suffered in his heart upon the sea, struggling for his own life
and the safe return of his companions. Yet even so he could not save his companions,
though he wished it; they perished through their own blind folly."""
    
    add_document("greek_myth", "The Odyssey - Opening", odyssey_content,
                metadata={"hero": "Odysseus", "epic": "odyssey", "type": "literature"})
    
    # Document 3: Hercules content  
    hercules_content = """Hercules, the strongest of all mortals, was the son of Zeus and the mortal woman Alcmene.
Hera, jealous of Zeus's affair, sent serpents to kill the infant Hercules, but he strangled them with his bare hands.
Later, driven mad by Hera, he killed his wife and children, leading to his famous Twelve Labors as penance.
These labors included slaying the Nemean Lion, capturing Cerberus from the underworld, and cleaning the Augean stables."""
    
    add_document("greek_myth", "Hercules: Hero of Strength", hercules_content,
                metadata={"hero": "Hercules", "parent": "Zeus", "type": "mythology"})
    
    # Document 4: Athena content
    athena_content = """Athena, goddess of wisdom and warfare, sprang fully grown from Zeus's head.
She was the patron goddess of Athens and helped many heroes including Odysseus and Perseus.
Her sacred symbols were the owl and the olive tree. Unlike Ares, who represented the brutal aspects of war,
Athena embodied strategic warfare and was known for her intelligence and counsel."""
    
    add_document("greek_myth", "Athena: Goddess of Wisdom", athena_content,
                metadata={"deity": "Athena", "domain": "wisdom", "parent": "Zeus", "type": "mythology"})

    # Build relationships
    print("\n🔗 Building relationships...")
    response = requests.post(f"{PROSE_STORE_URL}/worlds/greek_myth/aggregate", 
                           json={"window_size": 2})
    if response.status_code == 200:
        print("✅ Relationships built successfully")
    else:
        print(f"❌ Failed to build relationships: {response.status_code}")

if __name__ == "__main__":
    populate_mythology_world()
    print("\n🎉 Prose Store populated with mythology content!")
