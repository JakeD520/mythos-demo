"""
Island Builder - Chunks corpus, embeds, builds FAISS index and thresholds
"""
import os
import json
import time
import glob
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from sentence_transformers import SentenceTransformer

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False
    faiss = None


def read_txts(paths: List[str]) -> List[Tuple[str, str]]:
    """Read text files and return (filename, content) pairs"""
    docs = []
    for p in paths:
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().strip()
                if content:  # Only include non-empty files
                    docs.append((os.path.basename(p), content))
        except Exception as e:
            print(f"Warning: Could not read {p}: {e}")
    return docs


def chunk_text(text: str, target_words: int = 100, overlap_words: int = 20) -> List[str]:
    """
    Simple word-based chunker with sliding window
    """
    words = text.split()
    if len(words) <= target_words:
        return [text] if text.strip() else []
    
    chunks = []
    step = max(1, target_words - overlap_words)
    
    for i in range(0, len(words), step):
        chunk_words = words[i:i + target_words]
        chunk = " ".join(chunk_words)
        if chunk.strip():
            chunks.append(chunk)
        
        # Stop if we've reached the end
        if i + target_words >= len(words):
            break
    
    return chunks


def embed_chunks(model: SentenceTransformer, chunks: List[str], batch_size: int = 64) -> np.ndarray:
    """
    Embed chunks using sentence transformers, return L2-normalized vectors
    """
    if not chunks:
        return np.array([]).reshape(0, model.get_sentence_embedding_dimension())
    
    print(f"Embedding {len(chunks)} chunks...")
    vecs = model.encode(
        chunks, 
        batch_size=batch_size, 
        show_progress_bar=True, 
        convert_to_numpy=True, 
        normalize_embeddings=True  # L2 normalize
    )
    return vecs.astype(np.float32)


def build_faiss_index(X: np.ndarray, M: int = 32, efC: int = 200) -> Optional[Any]:
    """
    Build FAISS HNSW index if available
    """
    if not HAS_FAISS or X.shape[0] == 0:
        return None
    
    d = X.shape[1]
    index = faiss.IndexHNSWFlat(d, M)
    index.hnsw.efConstruction = efC
    index.add(X)
    return index


def brute_force_knn(X: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Brute force k-NN using numpy (fallback when FAISS not available)
    """
    n = X.shape[0]
    distances = np.zeros((n, k + 1))
    indices = np.zeros((n, k + 1), dtype=int)
    
    for i in range(n):
        # Compute distances to all other points
        dists = np.linalg.norm(X - X[i], axis=1)
        # Get k+1 nearest (including self)
        nearest_idx = np.argpartition(dists, k)[:k + 1]
        nearest_idx = nearest_idx[np.argsort(dists[nearest_idx])]
        
        distances[i] = dists[nearest_idx]
        indices[i] = nearest_idx
    
    return distances, indices


def compute_avg_knn_distances(X: np.ndarray, index: Optional[Any] = None, k: int = 8) -> np.ndarray:
    """
    Compute average k-NN distances for threshold calibration
    """
    n_samples = X.shape[0]
    # Adjust k if we have fewer samples than k+1
    effective_k = min(k, n_samples - 1)
    
    if effective_k <= 0:
        # If we only have 1 sample, return a default distance
        return np.array([0.5])
    
    if index is not None and HAS_FAISS:
        # Use FAISS index
        D, I = index.search(X, effective_k + 1)  # k+1 to include self
        # Remove self-distance (first column) and average the rest
        return D[:, 1:effective_k+1].mean(axis=1)
    else:
        # Brute force fallback
        D, I = brute_force_knn(X, effective_k)
        return D[:, 1:effective_k+1].mean(axis=1)


def build_island(
    world_id: str,
    corpus_dir: str = "corpus",
    artifacts_dir: str = "artifacts",
    model_id: str = "sentence-transformers/all-MiniLM-L6-v2",
    target_words: int = 100,
    overlap_words: int = 20,
    k: int = 8,
    accept_q: float = 0.95,
    review_q: float = 0.99,
    sources: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Main island building function
    """
    
    # Setup paths
    world_corpus_dir = Path(corpus_dir) / world_id
    world_artifacts_dir = Path(artifacts_dir) / world_id
    world_artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    # Find source files
    if sources:
        files = []
        for pattern in sources:
            files.extend(glob.glob(str(world_corpus_dir / pattern)))
    else:
        files = list(glob.glob(str(world_corpus_dir / "*.txt")))
    
    if not files:
        raise ValueError(f"No source files found in {world_corpus_dir}")
    
    print(f"Found {len(files)} source files")
    
    # Load embedding model
    print(f"Loading model: {model_id}")
    model = SentenceTransformer(model_id)
    
    # Read and chunk texts
    print("Reading and chunking texts...")
    docs = read_txts(files)
    
    spans = []
    all_chunks = []
    
    for source, text in docs:
        chunks = chunk_text(text, target_words, overlap_words)
        for chunk in chunks:
            span_id = len(spans)
            spans.append({
                "span_id": span_id,
                "source": source,
                "text": chunk
            })
            all_chunks.append(chunk)
    
    if not all_chunks:
        raise ValueError("No chunks produced from corpus")
    
    print(f"Created {len(all_chunks)} chunks from {len(docs)} documents")
    
    # Embed chunks
    X = embed_chunks(model, all_chunks)
    
    # Build index
    print("Building search index...")
    index = build_faiss_index(X) if HAS_FAISS else None
    
    # Compute thresholds
    print(f"Computing thresholds with k={k}...")
    avg_distances = compute_avg_knn_distances(X, index, k)
    T_accept = float(np.quantile(avg_distances, accept_q))
    T_review = float(np.quantile(avg_distances, review_q))
    
    # Get manifold version (increment if exists)
    meta_path = world_artifacts_dir / "meta.json"
    manifold_version = 1
    if meta_path.exists():
        try:
            with open(meta_path, 'r') as f:
                old_meta = json.load(f)
                manifold_version = old_meta.get('manifold_version', 0) + 1
        except:
            pass
    
    # Save artifacts
    print("Saving artifacts...")
    
    # Save embeddings
    np.save(world_artifacts_dir / "X.npy", X)
    
    # Save spans
    with open(world_artifacts_dir / "spans.jsonl", "w", encoding="utf-8") as f:
        for span in spans:
            f.write(json.dumps(span, ensure_ascii=False) + "\n")
    
    # Save FAISS index if available
    if index is not None:
        faiss.write_index(index, str(world_artifacts_dir / "index.faiss"))
    
    # Save metadata
    meta = {
        "world_id": world_id,
        "manifold_version": manifold_version,
        "model_id": model_id,
        "k": k,
        "T_accept": T_accept,
        "T_review": T_review,
        "target_words": target_words,
        "overlap_words": overlap_words,
        "accept_q": accept_q,
        "review_q": review_q,
        "num_chunks": len(all_chunks),
        "dim": int(X.shape[1]),
        "has_faiss_index": index is not None,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_files": [os.path.basename(f) for f in files]
    }
    
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    
    print(f"Island built successfully!")
    print(f"  Chunks: {len(all_chunks)}")
    print(f"  Dimensions: {X.shape[1]}")
    print(f"  T_accept: {T_accept:.4f}")
    print(f"  T_review: {T_review:.4f}")
    print(f"  Manifold version: {manifold_version}")
    
    return meta


if __name__ == "__main__":
    # Demo build
    meta = build_island(
        world_id="greek_myth",
        model_id="sentence-transformers/all-MiniLM-L6-v2"
    )
    print("Build complete:", json.dumps(meta, indent=2))
