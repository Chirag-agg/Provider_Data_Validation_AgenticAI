from datetime import datetime
from typing import Dict, Any, Optional
from .sanction_checker import check_provider
from ..compliance_store import upsert_status, get_status


def calculate_cri(provider_data: Dict[str, Any], validation_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Calculate Compliance Risk Index (CRI) for a provider.
    CRI = 0-100 where 0 = no risk, 100 = critical risk.
    
    Factors:
    - Sanction matches: +50 per match
    - Validation failures: +20 per failed verification
    - Missing credentials: +10 per missing item
    - Age of data: +5 if >90 days old
    """
    cri = 0
    factors = []
    
    # Sanction check
    sanction_result = check_provider(provider_data)
    if sanction_result["has_sanction"]:
        sanction_penalty = len(sanction_result["matches"]) * 50
        cri += min(sanction_penalty, 60)  # Cap sanction penalty at 60
        factors.append(f"Sanction matches: {len(sanction_result['matches'])}")
    
    # Validation failures
    if validation_result:
        failed_checks = sum(1 for check in validation_result.get("checks", []) if not check.get("passed", True))
        if failed_checks > 0:
            cri += failed_checks * 20
            factors.append(f"Failed validations: {failed_checks}")
    
    # Missing credentials
    missing = []
    if not provider_data.get("npi"):
        missing.append("NPI")
    if not provider_data.get("license"):
        missing.append("License")
    if not provider_data.get("board_certified"):
        missing.append("Board Certification")
    
    if missing:
        cri += len(missing) * 10
        factors.append(f"Missing: {', '.join(missing)}")
    
    # Data age
    updated_at = provider_data.get("updated_at") or provider_data.get("created_at")
    if updated_at:
        try:
            last_update = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            age_days = (datetime.utcnow() - last_update.replace(tzinfo=None)).days
            if age_days > 90:
                cri += 5
                factors.append(f"Stale data: {age_days} days old")
        except:
            pass
    
    cri = min(cri, 100)  # Cap at 100
    
    # Determine risk level
    if cri == 0:
        level = "NONE"
        color = "green"
    elif cri < 30:
        level = "LOW"
        color = "green"
    elif cri < 60:
        level = "MEDIUM"
        color = "yellow"
    elif cri < 80:
        level = "HIGH"
        color = "orange"
    else:
        level = "CRITICAL"
        color = "red"
    
    result = {
        "provider_id": provider_data.get("id", "unknown"),
        "cri_score": cri,
        "risk_level": level,
        "risk_color": color,
        "factors": factors,
        "sanction_matches": sanction_result["matches"],
        "calculated_at": datetime.utcnow().isoformat()
    }
    
    # Store result
    upsert_status(result)
    
    return result


def get_provider_compliance(provider_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve stored compliance status for a provider."""
    return get_status(provider_id)


def recalculate_all_compliance(providers: list) -> Dict[str, Any]:
    """Batch recalculate compliance for all providers."""
    results = []
    for provider in providers:
        cri = calculate_cri(provider)
        results.append(cri)
    
    return {
        "recalculated": len(results),
        "summary": {
            "critical": sum(1 for r in results if r["risk_level"] == "CRITICAL"),
            "high": sum(1 for r in results if r["risk_level"] == "HIGH"),
            "medium": sum(1 for r in results if r["risk_level"] == "MEDIUM"),
            "low": sum(1 for r in results if r["risk_level"] == "LOW"),
            "none": sum(1 for r in results if r["risk_level"] == "NONE")
        }
    }
