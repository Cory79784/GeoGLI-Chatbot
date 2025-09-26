"""
Rule-based intent router for geoGLI queries
Supports 3+1 intents: ask.country, commit.region, commit.country, law.lookup
"""
import re
from typing import Dict, Any


def route(query: str) -> Dict[str, Any]:
    """
    Route query to appropriate intent based on keywords and patterns
    
    Args:
        query: User query string
        
    Returns:
        Dict with intent, country, region, indicator, period slots
    """
    query_lower = query.lower()
    
    # Initialize slots
    slots = {
        "intent": "ask.country",  # default
        "country": "",
        "region": "",
        "indicator": "",
        "period": ""
    }
    
    # Extract country aliases
    country_aliases = {
        "saudi": "Saudi Arabia",
        "ksa": "Saudi Arabia", 
        "沙特": "Saudi Arabia",
        "saudi arabia": "Saudi Arabia"
    }
    
    for alias, country in country_aliases.items():
        if alias in query_lower:
            slots["country"] = country
            break
    
    # Default country if none found
    if not slots["country"]:
        slots["country"] = "Saudi Arabia"
    
    # Extract region aliases
    region_aliases = {
        "mena": "Middle East and North Africa",
        "middle east and north africa": "Middle East and North Africa",
        "middle east": "Middle East and North Africa",
        "north africa": "Middle East and North Africa",
        "sub-saharan africa": "Sub-Saharan Africa",
        "sub saharan africa": "Sub-Saharan Africa", 
        "ssa": "Sub-Saharan Africa",
        "africa": "Sub-Saharan Africa",  # TODO: NEED YOUR INPUT - more specific region mapping
        # TODO: Add more region aliases as needed
        "asia": "Asia",
        "europe": "Europe",
        "americas": "Americas",
        "oceania": "Oceania"
    }
    
    for alias, region in region_aliases.items():
        if alias in query_lower:
            slots["region"] = region
            break
    
    # Extract period using regex
    # Pattern 1: "2001-2017", "2001 - 2017"
    period_match = re.search(r"(\d{4})\s*-\s*(\d{4})", query)
    if period_match:
        slots["period"] = f"{period_match.group(1)}-{period_match.group(2)}"
    else:
        # Pattern 2: "last 5 years", "最近5年"
        recent_match = re.search(r"last\s+(\d+)\s+years|最近(\d+)年", query_lower)
        if recent_match:
            years = recent_match.group(1) or recent_match.group(2)
            slots["period"] = f"last {years} years"
    
    # Extract basic indicators (can be expanded)
    indicator_keywords = {
        "wildfire": "wildfires",
        "fire": "wildfires", 
        "drought": "drought",
        "vegetation": "vegetation productivity",
        "carbon": "soil organic carbon",
        "degradation": "land degradation",
        "productivity": "vegetation productivity"
    }
    
    for keyword, indicator in indicator_keywords.items():
        if keyword in query_lower:
            slots["indicator"] = indicator
            break
    
    # Intent routing with precedence
    # 1. Law/legislation intent (highest priority)
    law_keywords = ["law", "act", "regulation", "legislation", "法规", "条例", "细则"]
    if any(keyword in query_lower for keyword in law_keywords):
        slots["intent"] = "law.lookup"
        return slots
    
    # 2. Commitment intents
    commitment_keywords = ["commitment", "承诺", "restore", "restoration"]
    if any(keyword in query_lower for keyword in commitment_keywords):
        # Check if it's by region or by country
        region_indicators = ["region", "by region", "地区", "区域"]
        country_indicators = ["country", "by country", "国家"]
        
        if any(indicator in query_lower for indicator in region_indicators):
            slots["intent"] = "commit.region"
        elif any(indicator in query_lower for indicator in country_indicators):
            slots["intent"] = "commit.country"
        else:
            # Default to country-level commitments if ambiguous
            slots["intent"] = "commit.country"
        return slots
    
    # 3. Default: ask.country (GeoGLI cards)
    slots["intent"] = "ask.country"
    return slots


# Test function for development
def _test_router():
    """Test cases for the intent router"""
    test_cases = [
        ("show Saudi wildfire trend", "ask.country"),
        ("MENA restoration commitments by region", "commit.region"), 
        ("Saudi commitments by country", "commit.country"),
        ("Saudi logging law 2020", "law.lookup"),
        ("drought in KSA 2015-2020", "ask.country"),
        ("沙特法规", "law.lookup"),
        ("restoration by region", "commit.region")
    ]
    
    for query, expected_intent in test_cases:
        result = route(query)
        print(f"Query: '{query}' -> Intent: {result['intent']} (expected: {expected_intent})")
        print(f"  Slots: {result}")
        print()


if __name__ == "__main__":
    _test_router()


