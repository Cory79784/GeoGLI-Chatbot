"""
BM25 search store for JSONL documents
Minimal wrapper over rank-bm25 with tokenization for English and Chinese text
"""
import json
import re
import os
from typing import List, Dict, Any, Optional, Callable
from rank_bm25 import BM25Okapi


class BM25Store:
    """
    BM25 wrapper for JSONL documents with configurable key fields
    """
    
    def __init__(self, jsonl_path: str, key_fields: List[str], filter_fn: Optional[Callable] = None):
        """
        Initialize BM25 store from JSONL file
        
        Args:
            jsonl_path: Path to JSONL file
            key_fields: List of document fields to index for search
            filter_fn: Optional function to filter documents during loading
        """
        self.jsonl_path = jsonl_path
        self.key_fields = key_fields
        self.filter_fn = filter_fn
        self.documents = []
        self.bm25 = None
        
        self._load_documents()
        self._build_index()
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for BM25 indexing
        Supports English alphanumeric + Chinese characters
        """
        if not text:
            return []
        
        # Lowercase and extract tokens: alphanumeric with dots/% + Chinese chars
        tokens = re.findall(r"[A-Za-z0-9\.%]+|[\u4e00-\u9fa5]+", text.lower())
        return tokens
    
    def _load_documents(self):
        """Load documents from JSONL file"""
        if not os.path.exists(self.jsonl_path):
            print(f"Warning: JSONL file not found: {self.jsonl_path}")
            return
        
        try:
            with open(self.jsonl_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        doc = json.loads(line)
                        
                        # Apply filter if provided
                        if self.filter_fn and not self.filter_fn(doc):
                            continue
                        
                        self.documents.append(doc)
                        
                    except json.JSONDecodeError as e:
                        print(f"Warning: Invalid JSON at line {line_num} in {self.jsonl_path}: {e}")
                        continue
            
            print(f"Loaded {len(self.documents)} documents from {self.jsonl_path}")
            
        except Exception as e:
            print(f"Error loading JSONL file {self.jsonl_path}: {e}")
    
    def _build_index(self):
        """Build BM25 index from loaded documents"""
        if not self.documents:
            print(f"No documents to index for {self.jsonl_path}")
            return
        
        # Extract and tokenize text from key fields
        corpus = []
        for doc in self.documents:
            # Combine text from all key fields
            text_parts = []
            for field in self.key_fields:
                if field in doc and doc[field]:
                    text_parts.append(str(doc[field]))
            
            combined_text = " ".join(text_parts)
            tokens = self._tokenize(combined_text)
            corpus.append(tokens)
        
        # Build BM25 index
        if corpus:
            self.bm25 = BM25Okapi(corpus)
            print(f"Built BM25 index for {len(corpus)} documents from {self.jsonl_path}")
        else:
            print(f"Warning: No text content found for indexing in {self.jsonl_path}")
    
    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """
        Search documents using BM25
        
        Args:
            query: Search query string
            k: Number of top results to return
            
        Returns:
            List of documents with added '_score' field
        """
        if not self.bm25 or not self.documents:
            return []
        
        # Tokenize query
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        
        # Get BM25 scores
        scores = self.bm25.get_scores(query_tokens)
        
        # Get top-k results
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        
        results = []
        for idx in top_indices[:k]:  # Take top k indices
            if idx < len(self.documents):
                doc = self.documents[idx].copy()
                doc["_score"] = float(scores[idx])
                results.append(doc)
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the store"""
        return {
            "jsonl_path": self.jsonl_path,
            "key_fields": self.key_fields,
            "document_count": len(self.documents),
            "indexed": self.bm25 is not None
        }


def build_all_stores() -> Dict[str, BM25Store]:
    """
    Build all BM25 stores for the application
    
    Returns:
        Dictionary of store name -> BM25Store instance
    """
    stores = {}
    
    # Store configurations: (name, jsonl_path, key_fields)
    # Handle different working directory contexts (from project root vs backend dir)
    corpus_base = "corpus" if os.path.exists("corpus") else "backend/corpus"
    
    store_configs = [
        ("geogli", f"{corpus_base}/geogli_saudi.jsonl", ["title", "section", "text"]),
        ("commit_region", f"{corpus_base}/commit_region.jsonl", ["region", "text"]),
        ("commit_country", f"{corpus_base}/commit_country.jsonl", ["country", "text"])
    ]
    
    for name, jsonl_path, key_fields in store_configs:
        try:
            store = BM25Store(jsonl_path, key_fields)
            stores[name] = store
            print(f"✓ Built BM25 store '{name}' with {len(store.documents)} documents")
            
        except Exception as e:
            print(f"✗ Failed to build BM25 store '{name}': {e}")
            # Create empty store to avoid KeyError later
            stores[name] = BM25Store("", key_fields)
    
    return stores


# Test function for development
def _test_bm25():
    """Test BM25 store functionality"""
    # Create a test JSONL file
    test_data = [
        {"id": "1", "title": "Saudi Arabia Wildfires", "text": "Wildfire area in Saudi Arabia showing increasing trend", "section": "Stressors"},
        {"id": "2", "title": "Drought Analysis", "text": "Drought conditions affecting vegetation productivity", "section": "Climate"},
        {"id": "3", "title": "土地退化", "text": "中文测试文档关于土地退化问题", "section": "Analysis"}
    ]
    
    # Write test file
    test_file = "/tmp/test_bm25.jsonl"
    with open(test_file, 'w', encoding='utf-8') as f:
        for item in test_data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    # Test BM25 store
    store = BM25Store(test_file, ["title", "text", "section"])
    
    # Test searches
    queries = ["wildfire Saudi", "drought vegetation", "土地"]
    for query in queries:
        results = store.search(query, k=2)
        print(f"\nQuery: '{query}'")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result.get('title', 'N/A')} (score: {result['_score']:.3f})")
    
    # Clean up
    os.unlink(test_file)


if __name__ == "__main__":
    _test_bm25()
