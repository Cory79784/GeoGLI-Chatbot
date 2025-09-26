"""FAISS vector store wrapper using IndexFlatIP (Inner Product)"""
import os
import json
from typing import List, Dict, Optional, Tuple
import numpy as np
import faiss


class FAISSVectorStore:
    """
    FAISS vector store wrapper for dense retrieval
    Uses IndexFlatIP (Inner Product) for similarity search
    Robust to dynamic dimension changes
    """
    
    def __init__(self, index_path: str = None):
        self.index_path = index_path or os.getenv("INDEX_PATH", "./storage/faiss")
        self.faiss_file = os.path.join(self.index_path, "index.faiss")
        self.meta_file = os.path.join(self.index_path, "metadata.json")
        self.info_file = os.path.join(self.index_path, "info.json")
        self.index: Optional[faiss.IndexFlatIP] = None
        self.metadata: List[Dict] = []
        self.dimension: Optional[int] = None
    
    def create_with_dim(self, dim: int):
        """Create a new FAISS index with specified dimension"""
        self.index = faiss.IndexFlatIP(dim)
        self.dimension = dim
        self.metadata = []
        os.makedirs(self.index_path, exist_ok=True)
        self._persist_info()
        print(f"Created new FAISS index with dimension {dim}")
    
    def _persist_info(self):
        """Persist dimension info to disk"""
        with open(self.info_file, "w", encoding="utf-8") as f:
            json.dump({"dim": self.dimension}, f)
    
    def add(self, vectors: List[List[float]], metadatas: List[Dict]):
        """
        Add vectors and their metadata to the index
        
        Args:
            vectors: List of embedding vectors
            metadatas: List of metadata dicts for each vector
        """
        arr = np.array(vectors, dtype="float32")
        
        if self.index is None:
            # Lazy create if not exists
            self.create_with_dim(arr.shape[1])
        
        if arr.shape[1] != self.dimension:
            raise ValueError(f"FAISS dim mismatch: {arr.shape[1]} vs {self.dimension}")
        
        # Normalize vectors for inner product similarity
        faiss.normalize_L2(arr)
        
        # Add to FAISS index
        self.index.add(arr)
        
        # Store metadata
        self.metadata.extend(metadatas)
        
        print(f"Added {len(vectors)} vectors to index. Total: {self.index.ntotal}")
    
    def search(self, vector: List[float], top_k: int = 6) -> List[Dict]:
        """
        Search for similar vectors
        
        Args:
            vector: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            List of matching documents with metadata and scores
        """
        if self.index is None or self.index.ntotal == 0:
            return []
        
        # Convert to numpy and normalize
        v = np.array([vector], dtype="float32")
        faiss.normalize_L2(v)
        
        # Search in FAISS index
        D, I = self.index.search(v, min(top_k, self.index.ntotal))
        
        results = []
        for score, idx in zip(D[0], I[0]):
            if idx == -1 or idx >= len(self.metadata):
                continue
            meta = self.metadata[idx]
            results.append({"score": float(score), "meta": meta})
        
        return results
    
    def save(self):
        """Save index and metadata to disk"""
        if self.index is None:
            raise RuntimeError("No index to save")
        
        # Save FAISS index
        faiss.write_index(self.index, self.faiss_file)
        
        # Save metadata
        with open(self.meta_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        
        # Save dimension info
        self._persist_info()
        
        print(f"Saved index with {self.index.ntotal} vectors to {self.index_path}")
    
    def load(self):
        """
        Load index and metadata from disk
        
        Raises:
            FileNotFoundError: If index files don't exist
            Exception: For other loading errors
        """
        if not (os.path.exists(self.faiss_file) and os.path.exists(self.info_file)):
            raise FileNotFoundError("FAISS index not found")
        
        # Load FAISS index
        self.index = faiss.read_index(self.faiss_file)
        
        # Load dimension info
        with open(self.info_file, "r", encoding="utf-8") as f:
            info = json.load(f)
        self.dimension = info["dim"]
        
        # Load metadata
        if os.path.exists(self.meta_file):
            with open(self.meta_file, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
        else:
            self.metadata = []
        
        print(f"Loaded index with {self.index.ntotal} vectors from {self.index_path}")
    
    def exists(self) -> bool:
        """
        Check if index files exist without loading them
        
        Returns:
            True if all required index files exist, False otherwise
        """
        return (
            os.path.exists(self.faiss_file)
            and os.path.exists(self.info_file)
            and os.path.exists(self.meta_file)
        )
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store"""
        if self.index is None:
            return {"status": "not_initialized"}
        
        return {
            "status": "loaded",
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "metadata_count": len(self.metadata)
        }


# Global instance
vector_store = FAISSVectorStore()

