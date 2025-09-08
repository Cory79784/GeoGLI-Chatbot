"""Embedding provider - BGE-M3 local by default, with env switch to OpenAI-compatible"""
import os
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingProvider:
    """
    Embedding provider that supports multiple backends
    Default: BGE-M3 local model
    Alternative: OpenAI-compatible API (placeholder)
    """
    
    def __init__(self):
        self.backend = os.getenv("EMBEDDING_BACKEND", "bge-m3")
        self.model: Optional[SentenceTransformer] = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the embedding model based on backend configuration"""
        if self.backend == "bge-m3":
            try:
                # BGE-M3 is a high-quality multilingual embedding model
                self.model = SentenceTransformer('BAAI/bge-m3')
                print(f"Loaded BGE-M3 embedding model")
            except Exception as e:
                print(f"Failed to load BGE-M3 model: {e}")
                # Fallback to a lighter model
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                print("Fallback to all-MiniLM-L6-v2 model")
        elif self.backend == "openai_compat":
            # TODO: Implement OpenAI-compatible embedding API
            print("OpenAI-compatible embedding backend not yet implemented")
            # Fallback to local model for now
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            raise ValueError(f"Unknown embedding backend: {self.backend}")
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Embed a single text string
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        if not self.model:
            raise RuntimeError("Embedding model not initialized")
        
        embedding = self.model.encode(text, normalize_embeddings=True)
        return embedding
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Embed a batch of texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Array of embedding vectors
        """
        if not self.model:
            raise RuntimeError("Embedding model not initialized")
        
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding vectors"""
        if not self.model:
            raise RuntimeError("Embedding model not initialized")
        
        # Get dimension by encoding a sample text
        sample_embedding = self.embed_text("sample")
        return sample_embedding.shape[0]


# Global instance
embedding_provider = EmbeddingProvider()

