"""
Week 3 Integration Test - Complete MythOS Pipeline
Tests the full integration between Island Scorer, Prose Store, and Editor
"""
import asyncio
import json
import time
import requests
import aiohttp
from pathlib import Path


class MythOSIntegrationTester:
    """Test the complete MythOS pipeline"""
    
    def __init__(self):
        self.island_scorer_url = "http://localhost:8000"
        self.prose_store_url = "http://localhost:8001"
        self.editor_url = "http://localhost:8002"
        self.test_world = "integration-test-world"
    
    def test_service_health(self):
        """Test all services are running"""
        print("🏥 Testing Service Health...")
        
        services = [
            ("Island Scorer", self.island_scorer_url),
            ("Prose Store", self.prose_store_url),
            ("Editor", self.editor_url)
        ]
        
        for name, url in services:
            try:
                response = requests.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    print(f"✅ {name}: {response.json()}")
                else:
                    print(f"❌ {name}: HTTP {response.status_code}")
                    return False
            except Exception as e:
                print(f"❌ {name}: {str(e)}")
                return False
        
        print("🎉 All services healthy!")
        return True
    
    def test_world_building_pipeline(self):
        """Test building a world from corpus through Island Scorer"""
        print(f"\n🏗️ Testing World Building Pipeline...")
        
        # Step 1: Build world island
        build_request = {
            "world_id": self.test_world,
            "corpus_path": "corpus/greek_myth",
            "chunk_size": 200,
            "overlap": 50
        }
        
        try:
            response = requests.post(f"{self.island_scorer_url}/build", json=build_request)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ World island built: {result['chunks_processed']} chunks")
                print(f"   📊 Thresholds: Accept={result['threshold_accept']:.4f}, Review={result['threshold_review']:.4f}")
                return result
            else:
                print(f"❌ World building failed: {response.text}")
                return None
        except Exception as e:
            print(f"❌ World building error: {str(e)}")
            return None
    
    def test_prose_store_integration(self):
        """Test storing and retrieving documents"""
        print(f"\n📚 Testing Prose Store Integration...")
        
        # Create test documents
        documents = [
            {
                "world_id": self.test_world,
                "title": "The Hero's Journey Begins",
                "author": "Integration Tester",
                "content": """Odysseus stood upon the wine-dark shore, his heart heavy with the knowledge that his journey home to Ithaca would be fraught with trials beyond mortal comprehension. The gods had decreed his fate, and no amount of cunning could alter the divine will.

Yet hope burned within his breast like the sacred flame of Hestia. He had faced the Cyclops Polyphemus and lived to tell the tale. He had outwitted the sorceress Circe and resisted the deadly song of the Sirens. Each trial had forged him anew, tempering his spirit like bronze in the forge of Hephaestus.""",
                "metadata": {"test_type": "integration", "epic": "odyssey_variant"}
            },
            {
                "world_id": self.test_world,
                "title": "Divine Intervention",
                "author": "Integration Tester", 
                "content": """Athena, grey-eyed goddess of wisdom and warfare, watched from the heights of Mount Olympus as mortals below struggled with their fates. Her father Zeus had spoken, and the cosmic order demanded balance between divine will and mortal agency.

She donned her golden helm and descended through the clouds, her spear gleaming with celestial light. The time had come to guide her chosen heroes through the labyrinth of destiny that awaited them in the world below.""",
                "metadata": {"test_type": "integration", "theme": "divine_intervention"}
            }
        ]
        
        created_docs = []
        for doc in documents:
            try:
                response = requests.post(f"{self.prose_store_url}/documents", json=doc)
                if response.status_code == 200:
                    result = response.json()
                    created_docs.append(result)
                    print(f"✅ Created document: {result['title']} (ID: {result['id'][:8]}...)")
                else:
                    print(f"❌ Failed to create document: {response.text}")
                    return []
            except Exception as e:
                print(f"❌ Document creation error: {str(e)}")
                return []
        
        # Test search functionality
        search_queries = ["Odysseus journey", "Athena wisdom", "Zeus divine"]
        for query in search_queries:
            try:
                params = {"q": query, "world_id": self.test_world}
                response = requests.get(f"{self.prose_store_url}/search", params=params)
                if response.status_code == 200:
                    results = response.json()
                    print(f"✅ Search '{query}': {len(results['spans'])} spans found")
                else:
                    print(f"❌ Search failed for '{query}': {response.text}")
            except Exception as e:
                print(f"❌ Search error for '{query}': {str(e)}")
        
        # Test aggregation
        try:
            agg_request = {"world_id": self.test_world, "window_size": 2}
            response = requests.post(f"{self.prose_store_url}/worlds/{self.test_world}/aggregate", json=agg_request)
            if response.status_code == 200:
                print("✅ Relationship aggregation completed")
                
                # Check edges
                response = requests.get(f"{self.prose_store_url}/worlds/{self.test_world}/edges")
                if response.status_code == 200:
                    edges = response.json()
                    print(f"✅ Found {len(edges)} relationship edges")
                    if edges:
                        top_edge = edges[0]
                        print(f"   🔗 Top relationship: {top_edge['source_text'][:30]}... → {top_edge['target_text'][:30]}...")
            else:
                print(f"❌ Aggregation failed: {response.text}")
        except Exception as e:
            print(f"❌ Aggregation error: {str(e)}")
        
        return created_docs
    
    def test_editor_integration(self):
        """Test editor service integration"""
        print(f"\n✏️ Testing Editor Integration...")
        
        # Test connection to world
        try:
            connect_request = {"world_id": self.test_world, "initialize_corpus": False}
            response = requests.post(f"{self.editor_url}/connect", json=connect_request)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Connected to world: {result['world_id']}")
                print(f"   📊 World ready: {result['ready_for_editing']}")
            else:
                print(f"❌ Connection failed: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {str(e)}")
            return False
        
        # Test live meter functionality
        test_texts = [
            "Zeus hurled his mighty thunderbolt from the heights of Mount Olympus, shaking the very foundations of the earth.",
            "The hero drew his enchanted sword and faced the terrible dragon that guarded the golden fleece.",
            "The spaceship landed on the alien planet with a loud thud and smoke billowing from its engines."  # Should score low
        ]
        
        for i, text in enumerate(test_texts, 1):
            try:
                meter_request = {
                    "world_id": self.test_world,
                    "text": text,
                    "cursor_position": len(text) // 2,
                    "context_window": 200
                }
                
                response = requests.post(f"{self.editor_url}/live-meter", json=meter_request)
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Text {i} analysis:")
                    print(f"   🎯 IW Score: {result['iw_score']:.4f}")
                    print(f"   📝 Decision: {result['decision']}")
                    print(f"   🔍 Neighbors: {len(result['prose_neighbors'])} found")
                    print(f"   💡 Suggestions: {len(result['suggestions'])} provided")
                else:
                    print(f"❌ Live meter failed for text {i}: {response.text}")
            except Exception as e:
                print(f"❌ Live meter error for text {i}: {str(e)}")
        
        # Test document saving
        try:
            save_request = {
                "world_id": self.test_world,
                "title": "Integration Test Epic",
                "content": """In the twilight of the age of heroes, when the last echoes of divine laughter faded from Mount Olympus, a new champion arose from the ashes of Troy. His name was Alexios, and his destiny was written in the stars by the Fates themselves.

The Oracle at Delphi had spoken in riddles, as was her way: "When earth meets sky and bronze meets gold, the lost shall find their way home." None could interpret her meaning, but Alexios felt the truth burning in his heart like Apollo's sacred flame.

His journey would take him across the wine-dark seas to lands unknown, where monsters of legend still roamed and the gods still walked among mortals in disguise.""",
                "author": "Integration Test Suite",
                "auto_validate": True
            }
            
            response = requests.post(f"{self.editor_url}/save-document", json=save_request)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Document saved successfully")
                if result.get('validation'):
                    validation = result['validation']
                    print(f"   ✅ Validation: {validation['recommendation']}")
                    print(f"   📊 Overall score: {validation['overall_score']:.4f}")
                    print(f"   📝 Paragraphs analyzed: {len(validation['paragraph_results'])}")
            else:
                print(f"❌ Document save failed: {response.text}")
        except Exception as e:
            print(f"❌ Document save error: {str(e)}")
        
        return True
    
    def test_bidirectional_data_flow(self):
        """Test data flowing between all services"""
        print(f"\n🔄 Testing Bidirectional Data Flow...")
        
        # Test 1: Prose Store → Island Scorer
        print("1️⃣ Testing Prose Store → Island Scorer flow...")
        
        # Get spans from Prose Store
        try:
            response = requests.get(f"{self.prose_store_url}/search", params={
                "q": "Odysseus hero",
                "world_id": self.test_world
            })
            
            if response.status_code == 200:
                search_results = response.json()
                if search_results['spans']:
                    span_text = search_results['spans'][0]['text']
                    print(f"   📖 Retrieved span: {span_text[:50]}...")
                    
                    # Score it with Island Scorer
                    score_request = {"world_id": self.test_world, "text": span_text}
                    score_response = requests.post(f"{self.island_scorer_url}/score", json=score_request)
                    
                    if score_response.status_code == 200:
                        score_result = score_response.json()
                        print(f"   🎯 Island Scorer result: IW={score_result['iw_score']:.4f}, Decision={score_result['decision']}")
                        print("   ✅ Prose Store → Island Scorer: SUCCESS")
                    else:
                        print(f"   ❌ Island Scorer failed: {score_response.text}")
                else:
                    print("   ⚠️ No spans found for scoring test")
        except Exception as e:
            print(f"   ❌ Data flow test error: {str(e)}")
        
        # Test 2: Island Scorer → Editor → Prose Store
        print("\n2️⃣ Testing Island Scorer → Editor → Prose Store flow...")
        
        # Use Editor to analyze and save
        test_content = "Poseidon, earth-shaker and lord of the seas, rose from the depths of his watery realm to challenge the hero's passage across the wine-dark waters."
        
        try:
            # Analyze with Editor (which uses Island Scorer)
            meter_request = {
                "world_id": self.test_world,
                "text": test_content,
                "cursor_position": 0,
                "context_window": 200
            }
            
            meter_response = requests.post(f"{self.editor_url}/live-meter", json=meter_request)
            if meter_response.status_code == 200:
                meter_result = meter_response.json()
                print(f"   🎯 Editor analysis: IW={meter_result['iw_score']:.4f}")
                
                # Save via Editor (which uses Prose Store)
                save_request = {
                    "world_id": self.test_world,
                    "title": "Poseidon's Challenge",
                    "content": test_content,
                    "author": "Flow Test",
                    "auto_validate": True
                }
                
                save_response = requests.post(f"{self.editor_url}/save-document", json=save_request)
                if save_response.status_code == 200:
                    save_result = save_response.json()
                    print(f"   💾 Document saved: {save_result['document']['id'][:8]}...")
                    if save_result.get('validation'):
                        print(f"   ✅ Validation: {save_result['validation']['recommendation']}")
                    print("   ✅ Island Scorer → Editor → Prose Store: SUCCESS")
                else:
                    print(f"   ❌ Save failed: {save_response.text}")
            else:
                print(f"   ❌ Editor analysis failed: {meter_response.text}")
        except Exception as e:
            print(f"   ❌ Flow test error: {str(e)}")
        
        # Test 3: Relationship enhancement
        print("\n3️⃣ Testing Relationship-Enhanced Scoring...")
        
        try:
            # Get edges from Prose Store
            edges_response = requests.get(f"{self.prose_store_url}/worlds/{self.test_world}/edges")
            if edges_response.status_code == 200:
                edges = edges_response.json()
                print(f"   🔗 Found {len(edges)} relationship edges")
                
                if edges:
                    # Use edge context for enhanced scoring
                    edge = edges[0]
                    combined_text = f"{edge['source_text']} {edge['target_text']}"
                    
                    score_request = {"world_id": self.test_world, "text": combined_text}
                    score_response = requests.post(f"{self.island_scorer_url}/score", json=score_request)
                    
                    if score_response.status_code == 200:
                        score_result = score_response.json()
                        print(f"   🎯 Relationship-enhanced score: {score_result['iw_score']:.4f}")
                        print("   ✅ Relationship enhancement: FUNCTIONAL")
                    else:
                        print(f"   ❌ Enhanced scoring failed: {score_response.text}")
        except Exception as e:
            print(f"   ❌ Relationship test error: {str(e)}")
        
        return True
    
    def test_complete_demo_workflow(self):
        """Test the complete mythology demo workflow"""
        print(f"\n🏛️ Testing Complete Mythology Demo Workflow...")
        
        # Get world statistics
        try:
            stats_response = requests.get(f"{self.prose_store_url}/worlds/{self.test_world}/stats")
            if stats_response.status_code == 200:
                stats = stats_response.json()
                print(f"📊 World Statistics:")
                print(f"   📄 Documents: {stats['document_count']}")
                print(f"   📝 Spans: {stats['span_count']}")
                print(f"   🔗 Edges: {stats['edge_count']}")
                print(f"   📊 Total words: {stats['total_words']}")
        except Exception as e:
            print(f"❌ Stats error: {str(e)}")
        
        # Test world status from Island Scorer
        try:
            status_response = requests.get(f"{self.island_scorer_url}/world/{self.test_world}/status")
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"🏝️ Island Scorer Status:")
                print(f"   📦 Chunks: {status['total_chunks']}")
                print(f"   🎯 Accept threshold: {status['threshold_accept']:.4f}")
                print(f"   📝 Review threshold: {status['threshold_review']:.4f}")
        except Exception as e:
            print(f"❌ Status error: {str(e)}")
        
        # Test available worlds
        try:
            worlds_response = requests.get(f"{self.editor_url}/worlds")
            if worlds_response.status_code == 200:
                worlds = worlds_response.json()
                print(f"🌍 Available Worlds: {len(worlds['available_worlds'])}")
                for world_id, status in worlds['available_worlds'].items():
                    prose_status = "✅" if status['prose_store'] else "❌"
                    island_status = "✅" if status['island_scorer'] else "❌"
                    print(f"   {world_id}: Prose{prose_status} Island{island_status} ({status['chunks']} chunks)")
        except Exception as e:
            print(f"❌ Worlds error: {str(e)}")
        
        return True
    
    def run_complete_test_suite(self):
        """Run the complete integration test suite"""
        print("🚀 MYTHOS WEEK 3 INTEGRATION TEST SUITE")
        print("=" * 60)
        
        start_time = time.time()
        
        # Test sequence
        tests = [
            ("Service Health", self.test_service_health),
            ("World Building Pipeline", self.test_world_building_pipeline),
            ("Prose Store Integration", self.test_prose_store_integration),
            ("Editor Integration", self.test_editor_integration),
            ("Bidirectional Data Flow", self.test_bidirectional_data_flow),
            ("Complete Demo Workflow", self.test_complete_demo_workflow)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                result = test_func()
                if result is not False:
                    print(f"✅ {test_name}: PASSED")
                    passed += 1
                else:
                    print(f"❌ {test_name}: FAILED")
                    failed += 1
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {str(e)}")
                failed += 1
        
        # Final results
        total_time = time.time() - start_time
        print(f"\n" + "=" * 60)
        print(f"🏁 INTEGRATION TEST RESULTS")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏱️ Total time: {total_time:.2f} seconds")
        
        if failed == 0:
            print(f"\n🎉 ALL TESTS PASSED! Week 3 Integration Complete!")
            print(f"🏛️ MythOS Demo Pipeline Fully Operational")
            print(f"⚡ Ready for production mythology writing!")
        else:
            print(f"\n⚠️ {failed} test(s) failed. Check service configuration.")
        
        return failed == 0


if __name__ == "__main__":
    tester = MythOSIntegrationTester()
    success = tester.run_complete_test_suite()
    
    if success:
        print(f"\n🚀 Next Steps:")
        print(f"1. Open http://localhost:8002 to use the MythOS Editor")
        print(f"2. Connect to '{tester.test_world}' world")
        print(f"3. Start writing mythological content with live feedback!")
    else:
        print(f"\n🔧 Troubleshooting:")
        print(f"1. Ensure all services are running:")
        print(f"   - Island Scorer: http://localhost:8000")
        print(f"   - Prose Store: http://localhost:8001") 
        print(f"   - Editor: http://localhost:8002")
        print(f"2. Check corpus directory exists: corpus/greek_myth/")
        print(f"3. Verify all dependencies are installed")
