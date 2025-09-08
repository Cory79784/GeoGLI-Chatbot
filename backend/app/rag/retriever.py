"""Dense retrieval component using FAISS vector store"""
import os
from typing import List, Dict
from app.rag.embedder import embedding_provider
from app.rag.vectorstore import vector_store


class DenseRetriever:
    """
    Dense retrieval using embedding similarity search
    No BM25 or reranking - pure dense retrieval
    """
    
    def __init__(self):
        self.default_top_k = int(os.getenv("TOP_K", "6"))  # TODO: PERFORMANCE
        
        # Load vector store on initialization
        if not vector_store.load():
            print("Warning: No vector index found. Run ingestion first.")
    
    def retrieve(self, query: str, top_k: int = None) -> List[Dict]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: User query string
            top_k: Number of documents to retrieve (uses default if None)
            
        Returns:
            List of retrieved documents with metadata and scores
        """
        if top_k is None:
            top_k = self.default_top_k
        
        # Check if vector store is available
        stats = vector_store.get_stats()
        if stats["status"] != "loaded" or stats["total_vectors"] == 0:
            print("No documents in vector store")
            return []
        
        try:
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

