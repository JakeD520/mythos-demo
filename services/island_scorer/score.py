"""
Island Scorer - Loads artifacts and scores text against world canon
"""
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    faiss = None


class IslandScorer:
    """
    Loads island artifacts and scores text against canon
    """
    
    def __init__(self, artifacts_dir: str = "artifacts"):
        self.artifacts_dir = Path(artifacts_dir)
        self.loaded_worlds = {}  # Cache for loaded world data
    
    def load_world(self, world_id: str) -> Dict[str, Any]:
        """
        Load world artifacts if not already cached
        """
        if world_id in self.loaded_worlds:
            return self.loaded_worlds[world_id]
        
        world_dir = self.artifacts_dir / world_id
        meta_path = world_dir / "meta.json"
        
        if not meta_path.exists():
            raise ValueError(f"World '{world_id}' not found. Run build first.")
        
        # Load metadata
        with open(meta_path, 'r') as f:
            meta = json.load(f)
        
        # Load embeddings
        X_path = world_dir / "X.npy"
        if not X_path.exists():
            raise ValueError(f"Embeddings not found for world '{world_id}'")
        
        X = np.load(X_path)
        
        # Load spans
        spans_path = world_dir / "spans.jsonl"
        spans = []
        if spans_path.exists():
            with open(spans_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        spans.append(json.loads(line))
        
        # Load FAISS index if available
        index = None
        index_path = world_dir / "index.faiss"
        if HAS_FAISS and index_path.exists():
            try:
                index = faiss.read_index(str(index_path))
            except Exception as e:
                print(f"Warning: Could not load FAISS index: {e}")
        
        # Load embedding model
        model = SentenceTransformer(meta['model_id'])
        
        world_data = {
            'meta': meta,
            'X': X,
            'spans': spans,
            'index': index,
            'model': model
        }
        
        self.loaded_worlds[world_id] = world_data
        return world_data
    
    def get_world_status(self, world_id: str) -> Dict[str, Any]:
        """
        Get status information for a world
        """
        world_dir = self.artifacts_dir / world_id
        meta_path = world_dir / "meta.json"
        
        if not meta_path.exists():
            return {
                "world_id": world_id,
                "exists": False
            }
        
        try:
            with open(meta_path, 'r') as f:
                meta = json.load(f)
            
            return {
                "world_id": world_id,
                "exists": True,
                "manifold_version": meta.get('manifold_version'),
                "num_chunks": meta.get('num_chunks'),
                "model_id": meta.get('model_id'),
                "created_at": meta.get('created_at'),
                "T_accept": meta.get('T_accept'),
                "T_review": meta.get('T_review')
            }
        except Exception as e:
            return {
                "world_id": world_id,
                "exists": False,
                "error": str(e)
            }
    
    def brute_force_search(self, query_vec: np.ndarray, X: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Brute force k-NN search (fallback when FAISS not available)
        """
        distances = np.linalg.norm(X - query_vec, axis=1)
        indices = np.argsort(distances)[:k]
        return distances[indices], indices
    
    def score_text(self, world_id: str, text: str, k: int = 8) -> Dict[str, Any]:
        """
        Score text against world canon
        """
        world_data = self.load_world(world_id)
        
        meta = world_data['meta']
        X = world_data['X']
        spans = world_data['spans']
        index = world_data['index']
        model = world_data['model']
        
        # Embed the query text
        query_vec = model.encode([text], normalize_embeddings=True).astype(np.float32)
        query_vec = query_vec[0]  # Get single vector
        
        # Find nearest neighbors
        if index is not None and HAS_FAISS:
            # Use FAISS
            distances, indices = index.search(query_vec.reshape(1, -1), k)
            distances = distances[0]
            indices = indices[0]
        else:
            # Brute force fallback
            distances, indices = self.brute_force_search(query_vec, X, k)
        
        # Compute average distance (this is our main metric)
        avg_distance = float(np.mean(distances))
        
        # Compute iw_score (inverse of distance, normalized)
        # Higher score = more in-world
        max_possible_distance = 2.0  # For L2-normalized vectors
        iw_score = max(0.0, (max_possible_distance - avg_distance) / max_possible_distance)
        
        # Determine status based on thresholds
        T_accept = meta['T_accept']
        T_review = meta['T_review']
        
        if avg_distance <= T_accept:
            status = "ACCEPT"
        elif avg_distance <= T_review:
            status = "REVIEW"
        else:
            status = "REJECT"
        
        # Prepare neighbor information
        neighbors = []
        for i, (dist, idx) in enumerate(zip(distances, indices)):
            if idx < len(spans):
                span = spans[idx]
                neighbors.append({
                    "span_id": span['span_id'],
                    "source": span['source'],
                    "text": span['text'][:200] + "..." if len(span['text']) > 200 else span['text'],
                    "distance": float(dist)
                })
        
        return {
            "world_id": world_id,
            "text": text,
            "distance": avg_distance,
            "iw_score": iw_score,
            "status": status,
            "neighbors": neighbors,
            "thresholds": {
                "T_accept": T_accept,
                "T_review": T_review
            },
            "manifold_version": meta['manifold_version'],
            "model_id": meta['model_id']
        }
    
    def clear_cache(self, world_id: Optional[str] = None):
        """
        Clear cached world data
        """
        if world_id:
            self.loaded_worlds.pop(world_id, None)
        else:
            self.loaded_worlds.clear()


if __name__ == "__main__":
    # Demo scoring
    scorer = IslandScorer()
    
    test_cases = [
        "Orpheus played his lyre with divine skill.",  # Should ACCEPT
        "The bronze mirror reflected her beauty.",     # Should REVIEW  
        "Orpheus ignited his lightsaber dramatically." # Should REJECT
    ]
    
    for text in test_cases:
        try:
            result = scorer.score_text("greek_myth", text)
            print(f"\nText: {text}")
            print(f"Status: {result['status']}")
            print(f"Distance: {result['distance']:.4f}")
            print(f"IW Score: {result['iw_score']:.4f}")
            print(f"Top neighbor: {result['neighbors'][0]['source']} (dist: {result['neighbors'][0]['distance']:.4f})")
        except Exception as e:
            print(f"Error scoring '{text}': {e}")
