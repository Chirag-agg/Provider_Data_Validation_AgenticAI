"""Tests for validation service."""
import pytest
from src.provider_data_validation.models import ProviderInput
from src.provider_data_validation.services import ValidationService


def test_validate_provider_returns_result():
    """Test that validating a provider returns a ValidationResult."""
    provider = ProviderInput(
        provider_name="Dr. Sarah Johnson",
        phone="555-0123",
        address="123 Medical Center",
        specialty="Cardiology"
    )
    
    result = ValidationService.validate_provider(provider)
    
    assert result is not None
    assert result.provider_name == "Dr. Sarah Johnson"
    assert result.validation_status in ["VERIFIED", "PARTIALLY_VERIFIED", "UNVERIFIED", "FLAGGED"]


def test_normalize_name():
    """Test name normalization helper."""
    assert ValidationService._normalize_name("Dr. John Smith") == "dr. john smith"
    assert ValidationService._normalize_name("  JANE DOE  ") == "jane doe"
