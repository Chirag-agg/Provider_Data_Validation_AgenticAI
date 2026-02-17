"""Verification session storage.

This module prefers Redis for production persistence when `REDIS_URL` is
configured. When Redis is absent the module will try a SQL (Postgres)
fallback when `DATABASE_URL` is configured. Finally an in-memory dictionary
is used for development / demo environments.
"""

import json
from typing import Dict, Optional
from ..models import VerificationSession
from ..config import settings
from ..logger import logger


redis_client = None
if settings.REDIS_URL:
    try:
        import redis

        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        logger.info("Verification store: connected to Redis")
    except Exception as e:
        logger.warning(f"Could not connect to Redis at {settings.REDIS_URL}: {e}")


# Optional SQL fallback
db_available = False
try:
    if settings.database_url:
        from ..db import SessionLocal, VerificationSessionDB, init_db

        try:
            init_db()
        except Exception:
            pass

        db_available = True
        logger.info("Verification store: SQL fallback available")
except Exception:
    db_available = False


# In-memory fallback storage
_sessions: Dict[str, dict] = {}


def _to_dict(session) -> dict:
    if isinstance(session, VerificationSession):
        try:
            return session.model_dump()
        except Exception:
            # Fallback for pydantic v1 projects
            return session.dict()
    elif isinstance(session, dict):
        return session
    else:
        return {}


def create_session(session: VerificationSession) -> None:
    data = _to_dict(session)

    if redis_client:
        key = f"verification:session:{data['session_id']}"
        redis_client.set(key, json.dumps(data, default=str))
        # index by phone
        phone = data.get("phone")
        if phone:
            redis_client.set(f"verification:phone:{phone}", data["session_id"])
        return

    if db_available:
        db = SessionLocal()
        try:
            obj = db.query(VerificationSessionDB).filter_by(session_key=data["session_id"]).one_or_none()
            if obj is None:
                obj = VerificationSessionDB(
                    provider_id=data.get("provider_id"),
                    session_key=data["session_id"],
                    data=data,
                )
                db.add(obj)
            else:
                obj.data = data
                obj.provider_id = data.get("provider_id")
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
        return

    # fallback in-memory
    _sessions[data["session_id"]] = data


def get_session(session_id: str) -> Optional[dict]:
    if redis_client:
        key = f"verification:session:{session_id}"
        raw = redis_client.get(key)
        return json.loads(raw) if raw else None

    if db_available:
        db = SessionLocal()
        try:
            obj = db.query(VerificationSessionDB).filter_by(session_key=session_id).one_or_none()
            return obj.data if obj else None
        finally:
            db.close()

    return _sessions.get(session_id)


def get_session_by_phone(phone: str) -> Optional[dict]:
    if redis_client:
        sid = redis_client.get(f"verification:phone:{phone}")
        if sid:
            return get_session(sid)
        return None

    if db_available:
        db = SessionLocal()
        try:
            # This uses JSON lookup; some DB backends differ in syntax but
            # PostgreSQL + SQLAlchemy support this common pattern.
            obj = db.query(VerificationSessionDB).filter(VerificationSessionDB.data["phone"].astext == phone).first()
            return obj.data if obj else None
        finally:
            db.close()

    # fallback
    sid = None
    for s in _sessions.values():
        if s.get("phone") == phone:
            sid = s.get("session_id")
            break
    return get_session(sid) if sid else None


def update_session(session: VerificationSession) -> None:
    data = _to_dict(session)
    if not data:
        return
    if redis_client:
        key = f"verification:session:{data['session_id']}"
        redis_client.set(key, json.dumps(data, default=str))
        phone = data.get("phone")
        if phone:
            redis_client.set(f"verification:phone:{phone}", data["session_id"])
        return

    if db_available:
        db = SessionLocal()
        try:
            obj = db.query(VerificationSessionDB).filter_by(session_key=data["session_id"]).one_or_none()
            if obj is None:
                obj = VerificationSessionDB(
                    provider_id=data.get("provider_id"),
                    session_key=data["session_id"],
                    data=data,
                )
                db.add(obj)
            else:
                obj.data = data
                obj.provider_id = data.get("provider_id")
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
        return

    _sessions[data["session_id"]] = data


def delete_session(session_id: str) -> None:
    if redis_client:
        sess = get_session(session_id)
        if sess and sess.get("phone"):
            redis_client.delete(f"verification:phone:{sess.get('phone')}")
        redis_client.delete(f"verification:session:{session_id}")
        return

    if db_available:
        db = SessionLocal()
        try:
            obj = db.query(VerificationSessionDB).filter_by(session_key=session_id).one_or_none()
            if obj:
                db.delete(obj)
                db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
        return

    sess = _sessions.get(session_id)
    if sess and sess.get("phone"):
        _sessions.pop(session_id, None)


def get_all_sessions() -> Dict[str, dict]:
    if redis_client:
        keys = redis_client.keys("verification:session:*")
        out = {}
        for k in keys:
            sid = k.split(":")[-1]
            raw = redis_client.get(k)
            if raw:
                out[sid] = json.loads(raw)
        return out

    if db_available:
        out = {}
        db = SessionLocal()
        try:
            for obj in db.query(VerificationSessionDB).all():
                out[obj.session_key] = obj.data
        finally:
            db.close()
        return out

    return _sessions.copy()


def get_provider_sessions(provider_id: str) -> list:
    results = []
    for sess in get_all_sessions().values():
        pid = sess.get("provider_id")
        if pid == provider_id:
            results.append(sess)
    return results

