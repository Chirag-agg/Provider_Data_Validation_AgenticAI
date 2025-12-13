"""
Verification session storage.
In-memory store for tracking interactive provider verification conversations.
"""

from typing import Dict, Optional
from .models import VerificationSession

# In-memory storage for verification sessions
verification_sessions: Dict[str, VerificationSession] = {}

# Index by phone number for quick lookup when receiving SMS
phone_to_session: Dict[str, str] = {}


def create_session(session: VerificationSession) -> None:
    """Store a new verification session."""
    verification_sessions[session.session_id] = session
    phone_to_session[session.phone] = session.session_id


def get_session(session_id: str) -> Optional[VerificationSession]:
    """Retrieve a verification session by ID."""
    return verification_sessions.get(session_id)


def get_session_by_phone(phone: str) -> Optional[VerificationSession]:
    """Find active session by phone number."""
    session_id = phone_to_session.get(phone)
    if session_id:
        return verification_sessions.get(session_id)
    return None


def update_session(session: VerificationSession) -> None:
    """Update an existing session."""
    verification_sessions[session.session_id] = session


def delete_session(session_id: str) -> None:
    """Remove a session from storage."""
    session = verification_sessions.get(session_id)
    if session:
        # Remove from phone index
        if session.phone in phone_to_session:
            del phone_to_session[session.phone]
        # Remove from main storage
        del verification_sessions[session_id]


def get_all_sessions() -> Dict[str, VerificationSession]:
    """Get all verification sessions."""
    return verification_sessions.copy()


def get_provider_sessions(provider_id: str) -> list[VerificationSession]:
    """Get all verification sessions for a specific provider."""
    return [
        session for session in verification_sessions.values()
        if session.provider_id == provider_id
    ]
