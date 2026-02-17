import asyncio
import httpx
from datetime import datetime
from typing import List, Dict, Any
from ..compliance_store import upsert_sanction


OIG_EXCLUSIONS_URL = "https://oig.hhs.gov/exclusions/downloadables/UPDATED.csv"
SAM_API_KEY = None  # Set to enable SAM.gov API access


async def ingest_sanctions() -> Dict[str, Any]:
    """
    Download and store sanctions from OIG and SAM.gov.
    Returns summary statistics.
    """
    oig_count = await _ingest_oig()
    sam_count = await _ingest_sam()
    
    return {
        "ingestion_time": datetime.utcnow().isoformat(),
        "oig_records": oig_count,
        "sam_records": sam_count,
        "total": oig_count + sam_count
    }


async def _ingest_oig() -> int:
    """Download OIG-LEIE exclusion list and store."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(OIG_EXCLUSIONS_URL)
            resp.raise_for_status()
            lines = resp.text.strip().split("\n")
            headers = lines[0].lower().split(",")
            
            name_idx = headers.index("lastname") if "lastname" in headers else 0
            first_idx = headers.index("firstname") if "firstname" in headers else 1
            date_idx = headers.index("excldate") if "excldate" in headers else -1
            
            count = 0
            for line in lines[1:]:
                parts = line.split(",")
                if len(parts) < 3:
                    continue
                
                last = parts[name_idx].strip().strip('"')
                first = parts[first_idx].strip().strip('"') if first_idx < len(parts) else ""
                full_name = f"{first} {last}".strip()
                excl_date = parts[date_idx].strip().strip('"') if date_idx >= 0 and date_idx < len(parts) else ""
                
                if full_name:
                    upsert_sanction({
                        "full_name": full_name,
                        "source": "OIG-LEIE",
                        "effective_date": excl_date or "Unknown",
                        "reason": "Healthcare Exclusion",
                        "raw": line
                    })
                    count += 1
            
            return count
    except Exception as e:
        print(f"OIG ingestion error: {e}")
        return 0


async def _ingest_sam() -> int:
    """Download SAM.gov exclusions (requires API key)."""
    if not SAM_API_KEY:
        return 0  # Skip if no API key
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(
                "https://api.sam.gov/entity-information/v3/exclusions",
                params={"api_key": SAM_API_KEY, "includeSections": "entityInformation"},
                headers={"Accept": "application/json"}
            )
            resp.raise_for_status()
            data = resp.json()
            
            count = 0
            for entity in data.get("entityData", []):
                name = entity.get("legalBusinessName") or entity.get("entityName", "Unknown")
                effective = entity.get("exclusionDetails", {}).get("exclusionDate", "")
                
                upsert_sanction({
                    "full_name": name,
                    "source": "SAM.gov",
                    "effective_date": effective,
                    "reason": "Federal Exclusion",
                    "raw": str(entity)
                })
                count += 1
            
            return count
    except Exception as e:
        print(f"SAM ingestion error: {e}")
        return 0


if __name__ == "__main__":
    result = asyncio.run(ingest_sanctions())
    print(f"Ingestion complete: {result}")
