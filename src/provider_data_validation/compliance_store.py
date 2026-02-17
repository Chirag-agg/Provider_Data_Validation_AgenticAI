import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

DATA_DIR = Path(__file__).parent / "_compliance_data"
DATA_DIR.mkdir(exist_ok=True)
SANCTIONS_FILE = DATA_DIR / "sanction_registry.json"
STATUS_FILE = DATA_DIR / "provider_compliance_status.json"


def _load_json(path: Path) -> Any:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except Exception:
        return []


def _save_json(path: Path, data: Any):
    path.write_text(json.dumps(data, default=str, indent=2))


def load_sanctions() -> List[Dict[str, Any]]:
    return _load_json(SANCTIONS_FILE)


def save_sanctions(records: List[Dict[str, Any]]):
    _save_json(SANCTIONS_FILE, records)


def load_statuses() -> List[Dict[str, Any]]:
    return _load_json(STATUS_FILE)


def save_statuses(records: List[Dict[str, Any]]):
    _save_json(STATUS_FILE, records)


def upsert_sanction(record: Dict[str, Any]):
    records = load_sanctions()
    key = (record["full_name"], record["source"], record["effective_date"])
    existing = {(r["full_name"], r["source"], r["effective_date"]): i for i, r in enumerate(records)}
    if key in existing:
        records[existing[key]] = record
    else:
        records.append(record)
    save_sanctions(records)


def upsert_status(record: Dict[str, Any]):
    records = load_statuses()
    key = record["provider_id"]
    existing = {r["provider_id"]: i for i, r in enumerate(records)}
    if key in existing:
        records[existing[key]] = record
    else:
        records.append(record)
    save_statuses(records)


def get_status(provider_id: str) -> Optional[Dict[str, Any]]:
    return next((r for r in load_statuses() if r["provider_id"] == provider_id), None)
