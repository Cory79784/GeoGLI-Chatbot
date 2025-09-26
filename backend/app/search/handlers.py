"""
Intent handlers for BM25 search
Maps intents to appropriate BM25 stores and applies filtering logic
"""
from typing import List, Dict, Any, Optional


def handle_ask_country(query: str, slots: Dict[str, Any], stores: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Handle ask.country intent - search GeoGLI Saudi cards
    
    Args:
        query: Original user query
        slots: Parsed intent slots (country, indicator, period, etc.)
        stores: Dictionary of BM25Store instances
        
    Returns:
        List of matching documents with scores
    """
    if "geogli" not in stores or not stores["geogli"]:
        return []
    
    store = stores["geogli"]
    
    # Augment query with extracted slots for better matching
    search_terms = [query]
    
    # Add indicator if specified
    if slots.get("indicator"):
        search_terms.append(slots["indicator"])
    
    # Add period if specified  
    if slots.get("period"):
        search_terms.append(slots["period"])
    
    # Combine search terms
    augmented_query = " ".join(search_terms)
    
    # Search with higher k for country queries (more cards available)
    results = store.search(augmented_query, k=5)
    
    # Filter by country if different from Saudi Arabia
    country = slots.get("country", "")
    if country and country != "Saudi Arabia":
        # TODO: NEED YOUR INPUT - handle other countries when data available
        # For now, return empty results for non-Saudi queries
        results = []
    
    return results


def handle_commit_region(query: str, slots: Dict[str, Any], stores: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Handle commit.region intent - search regional commitment data
    
    Args:
        query: Original user query
        slots: Parsed intent slots
        stores: Dictionary of BM25Store instances
        
    Returns:
        List of matching regional commitment documents
    """
    if "commit_region" not in stores or not stores["commit_region"]:
        return []
    
    store = stores["commit_region"]
    
    # If specific region is extracted, try exact match first
    region = slots.get("region", "")
    if region:
        # Filter documents by exact region match
        exact_matches = []
        for doc in store.documents:
            if doc.get("region", "").lower() == region.lower():
                doc_with_score = doc.copy()
                doc_with_score["_score"] = 10.0  # High score for exact match
                exact_matches.append(doc_with_score)
        
        if exact_matches:
            return exact_matches[:3]  # Return up to 3 exact matches
    
    # Fall back to BM25 search
    search_query = query
    if region:
        search_query = f"{query} {region}"
    
    results = store.search(search_query, k=3)
    return results


def handle_commit_country(query: str, slots: Dict[str, Any], stores: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Handle commit.country intent - search country-level commitment data
    
    Args:
        query: Original user query
        slots: Parsed intent slots
        stores: Dictionary of BM25Store instances
        
    Returns:
        List of matching country commitment documents
    """
    if "commit_country" not in stores or not stores["commit_country"]:
        return []
    
    store = stores["commit_country"]
    
    # If specific country is extracted, try exact match first
    country = slots.get("country", "")
    if country:
        # Filter documents by exact country match
        exact_matches = []
        for doc in store.documents:
            if doc.get("country", "").lower() == country.lower():
                doc_with_score = doc.copy()
                doc_with_score["_score"] = 10.0  # High score for exact match
                exact_matches.append(doc_with_score)
        
        if exact_matches:
            return exact_matches[:3]  # Return up to 3 exact matches
    
    # Fall back to BM25 search
    search_query = query
    if country:
        search_query = f"{query} {country}"
    
    results = store.search(search_query, k=3)
    return results


def handle_law_lookup(query: str, slots: Dict[str, Any], stores: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Handle law.lookup intent - placeholder for legislation search
    
    Args:
        query: Original user query
        slots: Parsed intent slots  
        stores: Dictionary of BM25Store instances (unused for now)
        
    Returns:
        List with placeholder response
    """
    # TODO: NEED YOUR INPUT - implement actual legislation search
    # For MVP, return placeholder response
    placeholder_doc = {
        "id": "law_placeholder",
        "title": "Legislation Search - Coming Soon",
        "text": "Legislation and regulatory information search is currently under development. Please check back later for access to legal documents and regulations.",
        "placeholder": True,
        "intent": "law.lookup",
        "query": query,
        "_score": 1.0
    }
    
    # Add extracted country/region context if available
    if slots.get("country"):
        placeholder_doc["text"] += f" (Query context: {slots['country']})"
    if slots.get("region"):
        placeholder_doc["text"] += f" (Query context: {slots['region']})"
    
    return [placeholder_doc]


def format_hits_for_response(hits: List[Dict[str, Any]], intent: str) -> List[Dict[str, Any]]:
    """
    Format BM25 hits for consistent API response
    Ensures all required fields are present with sensible defaults
    
    Args:
        hits: Raw BM25 search results
        intent: Intent that generated these hits
        
    Returns:
        Formatted hits with consistent schema
    """
    formatted = []
    
    for hit in hits:
        formatted_hit = {
            "title": hit.get("title", ""),
            "text": hit.get("text", ""),
            "section": hit.get("section", ""),
            "country": hit.get("country", ""),
            "region": hit.get("region", ""),
            "images": hit.get("images", []),
            "citation_path": hit.get("citation_path", ""),
            "url": hit.get("url", ""),
            "source_csv": hit.get("source_csv", ""),
            "updated_at": hit.get("updated_at", ""),
            "_score": hit.get("_score", 0.0),
            "intent": intent
        }
        
        # Ensure images is a list
        if not isinstance(formatted_hit["images"], list):
            if formatted_hit["images"]:
                formatted_hit["images"] = [formatted_hit["images"]]
            else:
                formatted_hit["images"] = []
        
        # Add placeholder flag if present
        if hit.get("placeholder"):
            formatted_hit["placeholder"] = True
        
        formatted.append(formatted_hit)
    
    return formatted


# Test function for development
def _test_handlers():
    """Test handler functions with mock data"""
    from app.search.bm25_store import BM25Store
    
    # Mock stores (empty for testing)
    mock_stores = {
        "geogli": BM25Store("", ["title", "text"]),
        "commit_region": BM25Store("", ["region", "text"]),
        "commit_country": BM25Store("", ["country", "text"])
    }
    
    # Test cases
    test_cases = [
        {
            "query": "Saudi wildfire trend",
            "slots": {"intent": "ask.country", "country": "Saudi Arabia", "indicator": "wildfires"},
            "handler": handle_ask_country
        },
        {
            "query": "MENA restoration commitments",
            "slots": {"intent": "commit.region", "region": "Middle East and North Africa"},
            "handler": handle_commit_region
        },
        {
            "query": "Saudi commitments",
            "slots": {"intent": "commit.country", "country": "Saudi Arabia"},
            "handler": handle_commit_country
        },
        {
            "query": "logging law 2020",
            "slots": {"intent": "law.lookup", "country": "Saudi Arabia"},
            "handler": handle_law_lookup
        }
    ]
    
    for case in test_cases:
        print(f"\n🧪 Testing: {case['query']}")
        print(f"   Intent: {case['slots']['intent']}")
        
        results = case["handler"](case["query"], case["slots"], mock_stores)
        formatted = format_hits_for_response(results, case["slots"]["intent"])
        
        print(f"   Results: {len(formatted)} hits")
        for i, hit in enumerate(formatted, 1):
            print(f"     {i}. {hit.get('title', 'N/A')} (score: {hit.get('_score', 0):.3f})")


if __name__ == "__main__":
    _test_handlers()


