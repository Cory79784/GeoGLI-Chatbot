"""Dense retrieval component using FAISS vector store"""
import os
from typing import List, Dict
from app.rag.vectorstore import vector_store

# Lazy import for embedding provider to avoid initialization errors


class DenseRetriever:
    """
    Dense retrieval using embedding similarity search
    No BM25 or reranking - pure dense retrieval
    Uses lazy loading to avoid crashes during import
    """
    
    def __init__(self):
        self.default_top_k = int(os.getenv("TOP_K", "6"))  # TODO: PERFORMANCE
        self._index_loaded = False
        
        # Don't load vector store on initialization to avoid import-time crashes
        # Load will be attempted during first retrieval call
    
    def retrieve(self, query: str, top_k: int = None) -> List[Dict]:
        """
        Retrieve relevant documents for a query with lazy loading
        
        Args:
            query: User query string
            top_k: Number of documents to retrieve (uses default if None)
            
        Returns:
            List of retrieved documents with metadata and scores
            Returns empty list if index is missing or any error occurs
        """
        if top_k is None:
            top_k = self.default_top_k
        
        # Lazy load: try to load index only when needed
        if not self._index_loaded:
            try:
                vector_store.load()
                self._index_loaded = True
            except FileNotFoundError:
                # Index doesn't exist → return empty results for fallback to LLM
                print("Vector index not found - will fallback to direct LLM")
                return []
            except Exception as e:
                # Any other loading error → also return empty results
                import logging
                logging.getLogger(__name__).warning(f"Vector store load error: {e}")
                return []
        
        # Check if vector store has documents
        stats = vector_store.get_stats()
        if stats["status"] != "loaded" or stats.get("total_vectors", 0) == 0:
            print("No documents in vector store")
            return []
        
        try:
            # Lazy import embedding provider to avoid initialization errors
            from app.rag.embedder import embedding_provider
            
            # Embed the query
            query_vector = embedding_provider.embed_text(query)
            
            # Search for similar documents
            results = vector_store.search(query_vector, top_k)
            
            print(f"Retrieved {len(results)} documents for query: {query[:50]}...")
            
            return results
            
        except Exception as e:
            print(f"Error during retrieval: {e}")
            return []
    
    def get_retriever_stats(self) -> Dict:
        """Get statistics about the retriever and vector store"""
        stats = vector_store.get_stats()
        stats["default_top_k"] = self.default_top_k
        return stats


# Global instance
dense_retriever = DenseRetriever()

