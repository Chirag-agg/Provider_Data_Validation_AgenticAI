from rapidfuzz import fuzz
from typing import List, Dict, Any, Optional
from ..compliance_store import load_sanctions


MATCH_THRESHOLD = 80  # Fuzzy match threshold 0-100


def check_sanctions(provider_name: str, threshold: int = MATCH_THRESHOLD) -> List[Dict[str, Any]]:
    """
    Check if a provider name matches any sanctions using fuzzy matching.
    Returns list of matches with similarity scores.
    """
    sanctions = load_sanctions()
    matches = []
    
    for sanction in sanctions:
        score = fuzz.ratio(provider_name.lower(), sanction["full_name"].lower())
        if score >= threshold:
            matches.append({
                "matched_name": sanction["full_name"],
                "source": sanction["source"],
                "effective_date": sanction["effective_date"],
                "reason": sanction["reason"],
                "similarity_score": score
            })
    
    return sorted(matches, key=lambda x: x["similarity_score"], reverse=True)


def check_provider(provider_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check provider against multiple name variants.
    Returns comprehensive match result.
    """
    name_variants = [
        provider_data.get("full_name", ""),
        f"{provider_data.get('first_name', '')} {provider_data.get('last_name', '')}",
        provider_data.get("practice_name", "")
    ]
    
    all_matches = []
    for variant in name_variants:
        if variant.strip():
            matches = check_sanctions(variant)
            for match in matches:
                match["search_variant"] = variant
                all_matches.append(match)
    
    return {
        "provider_id": provider_data.get("id", "unknown"),
        "search_variants": [v for v in name_variants if v.strip()],
        "matches": all_matches,
        "has_sanction": len(all_matches) > 0,
        "highest_score": max([m["similarity_score"] for m in all_matches], default=0)
    }
