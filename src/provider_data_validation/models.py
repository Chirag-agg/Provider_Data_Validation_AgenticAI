"""
Pydantic models for Provider Data Validation System.
Defines request/response schemas for API endpoints.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class ConfidenceScores(BaseModel):
    """Confidence scores for different validation aspects."""
    identity_match: float = Field(..., ge=0, le=1, description="Identity match confidence (0-1)")
    license_validity: float = Field(..., ge=0, le=1, description="License validity confidence (0-1)")
    location_verified: float = Field(..., ge=0, le=1, description="Location verification confidence (0-1)")
    hospital_affiliation: float = Field(..., ge=0, le=1, description="Hospital affiliation confidence (0-1)")
    specialty_verified: float = Field(..., ge=0, le=1, description="Specialty verification confidence (0-1)")
    overall_confidence: float = Field(..., ge=0, le=1, description="Overall validation confidence (0-1)")


class LicenseInfo(BaseModel):
    """License information."""
    license_number: Optional[str] = None
    status: Optional[str] = None
    specialty: Optional[str] = None
    expiration_date: Optional[str] = None
    issuing_body: Optional[str] = None


class HospitalAffiliation(BaseModel):
    """Hospital affiliation details."""
    hospital_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    affiliation_status: Optional[str] = None


class RiskFlag(BaseModel):
    """Risk flag with severity level."""
    flag: str
    severity: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    description: Optional[str] = None


class ValidationIssue(BaseModel):
    """Validation issue details."""
    issue: str
    severity: str = Field(..., description="LOW, MEDIUM, HIGH, CRITICAL")
    source: str
    recommendation: Optional[str] = None


class ValidationResult(BaseModel):
    """Complete validation result for a single provider."""
    provider_id: str = Field(..., description="Unique identifier for the provider record")
    input_data: Dict[str, Any] = Field(..., description="Original input data")
    
    # Identity Information
    provider_name: str
    npi_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    
    # Verified Information
    verified_phone: Optional[str] = None
    verified_address: Optional[str] = None
    verified_specialty: Optional[str] = None
    
    # License Information
    license_info: Optional[LicenseInfo] = None
    
    # Hospital Affiliation
    hospital_affiliation: Optional[HospitalAffiliation] = None
    
    # Confidence Scores
    confidence_scores: ConfidenceScores
    
    # Data Sources Checked
    sources_checked: List[str] = Field(default_factory=list, description="List of data sources queried")
    sources_matched: List[str] = Field(default_factory=list, description="Sources with matching data")
    
    # Validation Details
    validation_status: str = Field(..., description="VERIFIED, PARTIALLY_VERIFIED, UNVERIFIED, FLAGGED")
    issues: List[ValidationIssue] = Field(default_factory=list)
    risk_flags: List[RiskFlag] = Field(default_factory=list)
    
    # Additional Information
    requires_manual_review: bool = False
    requires_contact_verification: bool = False
    next_steps: List[str] = Field(default_factory=list)
    
    # Metadata
    validation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: float = 0.0


class ProviderInput(BaseModel):
    """Input for validating a single provider."""
    provider_name: str = Field(..., min_length=1, description="Full name of the provider")
    phone: Optional[str] = None
    address: Optional[str] = None
    specialty: Optional[str] = None
    license_no: Optional[str] = None
    npi_number: Optional[str] = None
    hospital_affiliation: Optional[str] = None
    date_of_birth: Optional[str] = None


class BatchValidationRequest(BaseModel):
    """Request for batch validation of multiple providers."""
    providers: List[ProviderInput]
    priority: str = Field(default="normal", description="normal, high, low")
    notify_email: Optional[str] = None
    notify_webhook: Optional[str] = None


class FileUploadResponse(BaseModel):
    """Response after file upload."""
    file_id: str
    filename: str
    file_type: str
    providers_extracted: int
    extraction_status: str
    extracted_providers: List[ProviderInput]
    upload_timestamp: datetime = Field(default_factory=datetime.utcnow)


class BatchValidationResponse(BaseModel):
    """Response for batch validation request."""
    batch_id: str
    status: str = Field(..., description="QUEUED, PROCESSING, COMPLETED, FAILED")
    total_providers: int
    completed: int = 0
    failed: int = 0
    results: List[ValidationResult] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time_ms: float = 0.0


class SingleValidationResponse(BaseModel):
    """Response for single provider validation."""
    success: bool
    data: Optional[ValidationResult] = None
    error: Optional[str] = None
    processing_time_ms: float = 0.0


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    components: Dict[str, str] = Field(default_factory=dict)
    system_info: Dict[str, Any] = Field(default_factory=dict)


class ValidationStatsResponse(BaseModel):
    """Validation statistics response."""
    total_validations: int
    successful: int
    failed: int
    success_rate: float
    average_confidence: float
    most_common_issues: List[str]
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    code: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
