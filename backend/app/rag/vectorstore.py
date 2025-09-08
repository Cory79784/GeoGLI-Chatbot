"""FAISS vector store wrapper using IndexFlatIP (Inner Product)"""
import os
import pickle
import json
from typing import List, Dict, Optional, Tuple
import numpy as np
import faiss


class FAISSVectorStore:
    """
    FAISS vector store wrapper for dense retrieval
    Uses IndexFlatIP (Inner Product) for similarity search
    """
    
    def __init__(self, index_path: str = None):
        self.index_path = index_path or os.getenv("INDEX_PATH", "./storage/faiss")
        self.index: Optional[faiss.IndexFlatIP] = None
        self.metadata: List[Dict] = []
        self.dimension: Optional[int] = None
    
    def initialize_index(self, dimension: int):
        """Initialize a new FAISS index"""
        self.dimension = dimension
        # IndexFlatIP for inner product similarity (works well with normalized embeddings)
        self.index = faiss.IndexFlatIP(dimension)
        self.metadata = []
        print(f"Initialized new FAISS index with dimension {dimension}")
    
    def add_vectors(self, vectors: np.ndarray, metadata_list: List[Dict]):
        """
        Add vectors and their metadata to the index
        
        Args:
            vectors: Array of embedding vectors (normalized)
            metadata_list: List of metadata dicts for each vector
        """
        if self.index is None:
            raise RuntimeError("Index not initialized")
        
        if len(vectors) != len(metadata_list):
            raise ValueError("Number of vectors must match number of metadata entries")
        
        # Add vectors to FAISS index
        self.index.add(vectors.astype(np.float32))
        
        # Store metadata
        self.metadata.extend(metadata_list)
        
        print(f"Added {len(vectors)} vectors to index. Total: {self.index.ntotal}")
    
    def search(self, query_vector: np.ndarray, top_k: int = 6) -> List[Dict]:
        """
        Search for similar vectors
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            List of matching documents with metadata and scores
        """
        if self.index is None or self.index.ntotal == 0:
            return []
        
        # Ensure query vector is normalized and correct shape
        query_vector = query_vector.reshape(1, -1).astype(np.float32)
        
        # Search in FAISS index
        scores, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.metadata):  # Valid index
                result = self.metadata[idx].copy()
                result['score'] = float(score)
                results.append(result)
        
        return results
    
    def save(self):
        """Save index and metadata to disk"""
        if self.index is None:
            raise RuntimeError("No index to save")
        
        os.makedirs(self.index_path, exist_ok=True)
        
        # Save FAISS index
        index_file = os.path.join(self.index_path, "index.faiss")
        faiss.write_index(self.index, index_file)
        
        # Save metadata
        metadata_file = os.path.join(self.index_path, "metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
        
        # Save dimension info
        info_file = os.path.join(self.index_path, "info.json")
        with open(info_file, 'w') as f:
            json.dump({"dimension": self.dimension, "total_vectors": self.index.ntotal}, f)
        
        print(f"Saved index with {self.index.ntotal} vectors to {self.index_path}")
    
    def load(self) -> bool:
        """
        Load index and metadata from disk
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            index_file = os.path.join(self.index_path, "index.faiss")
            metadata_file = os.path.join(self.index_path, "metadata.json")
            info_file = os.path.join(self.index_path, "info.json")
            
            if not all(os.path.exists(f) for f in [index_file, metadata_file, info_file]):
                return False
            
            # Load FAISS index
            self.index = faiss.read_index(index_file)
            
            # Load metadata
            with open(metadata_file, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
            
            # Load dimension info
            with open(info_file, 'r') as f:
                info = json.load(f)
                self.dimension = info["dimension"]
            
            print(f"Loaded index with {self.index.ntotal} vectors from {self.index_path}")
            return True
            
        except Exception as e:
            print(f"Failed to load index: {e}")
            return False
    
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

