"""Tests for verification store persistence."""
import pytest
from src.provider_data_validation.tools.verification_store import (
    create_session, get_session, update_session, delete_session
)
from src.provider_data_validation.models import VerificationSession


def test_create_and_get_session():
    """Test session creation and retrieval."""
    session = VerificationSession(
        session_id="test-123",
        provider_id="provider-456",
        phone="+15551234567",
        verification_type="sms",
        status="pending"
    )
    
    create_session(session)
    retrieved = get_session("test-123")
    
    assert retrieved is not None
    assert retrieved["session_id"] == "test-123"
    assert retrieved["provider_id"] == "provider-456"
    
    # Cleanup
    delete_session("test-123")


def test_update_session():
    """Test updating a session."""
    session = VerificationSession(
        session_id="test-update",
        provider_id="provider-789",
        phone="+15559876543",
        verification_type="sms",
        status="pending"
    )
    
    create_session(session)
    
    # Update status
    session.status = "verified"
    update_session(session)
    
    retrieved = get_session("test-update")
    assert retrieved["status"] == "verified"
    
    # Cleanup
    delete_session("test-update")
