"""
Validation Service - Orchestrates provider validation across multiple crews and data sources.
Provides a unified interface for API layer to interact with validation logic.
"""

import json
import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import uuid
import time

from .models import (
    ProviderInput, ValidationResult, ConfidenceScores, 
    LicenseInfo, HospitalAffiliation, RiskFlag, ValidationIssue,
    BatchValidationResponse
)


class ValidationService:
    """Service to orchestrate provider validation."""
    
    # Paths to mock data
    BASE_PATH = Path(__file__).parent.parent.parent
    NPI_PATH = BASE_PATH / "mock_data" / "npi_registry.json"
    LICENSE_PATH = BASE_PATH / "mock_data" / "license_registry.json"
    HOSPITAL_PATH = BASE_PATH / "mock_data" / "hospital_roster.json"
    MAPS_PATH = BASE_PATH / "mock_data" / "maps_listing.json"
    CLINIC_PATH = BASE_PATH / "mock_data" / "clinic_website.html"
    
    # Storage for batch jobs
    batch_jobs: Dict[str, BatchValidationResponse] = {}
    
    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize provider name for matching."""
        return name.lower().strip()
    
    @staticmethod
    def _load_json(path: Path) -> Dict[str, Any]:
        """Load JSON file with error handling."""
        try:
            if path.exists():
                with open(path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading {path}: {e}")
        return {}
    
    @staticmethod
    def _load_html(path: Path) -> str:
        """Load HTML file with error handling."""
        try:
            if path.exists():
                with open(path, 'r') as f:
                    return f.read()
        except Exception as e:
            print(f"Error loading {path}: {e}")
        return ""
    
    @classmethod
    def _search_npi_registry(cls, provider_name: str, phone: Optional[str] = None) -> Optional[Dict]:
        """Search NPI registry for provider."""
        npi_data = cls._load_json(cls.NPI_PATH)
        normalized_name = cls._normalize_name(provider_name)
        
        for entry in npi_data.get("providers", []):
            if cls._normalize_name(entry.get("name", "")) == normalized_name:
                if phone:
                    # If phone provided, verify it matches
                    entry_phone = entry.get("phone", "").replace(" ", "").replace("-", "")
                    input_phone = phone.replace(" ", "").replace("-", "")
                    if entry_phone == input_phone:
                        return entry
                else:
                    return entry
        return None
    
    @classmethod
    def _search_license_registry(cls, provider_name: str, license_no: Optional[str] = None) -> Optional[Dict]:
        """Search license registry for provider."""
        license_data = cls._load_json(cls.LICENSE_PATH)
        normalized_name = cls._normalize_name(provider_name)
        
        for entry in license_data.get("licenses", []):
            if cls._normalize_name(entry.get("name", "")) == normalized_name:
                if license_no:
                    if entry.get("license_number", "") == license_no:
                        return entry
                else:
                    return entry
        return None
    
    @classmethod
    def _search_hospital_roster(cls, provider_name: str) -> Optional[Dict]:
        """Search hospital roster for provider."""
        hospital_data = cls._load_json(cls.HOSPITAL_PATH)
        normalized_name = cls._normalize_name(provider_name)
        
        for entry in hospital_data.get("roster", []):
            if cls._normalize_name(entry.get("name", "")) == normalized_name:
                return entry
        return None
    
    @classmethod
    def _search_maps_listing(cls, provider_name: str) -> Optional[Dict]:
        """Search maps listing for provider."""
        maps_data = cls._load_json(cls.MAPS_PATH)
        normalized_name = cls._normalize_name(provider_name)
        
        for entry in maps_data.get("businesses", []):
            if cls._normalize_name(entry.get("name", "")) == normalized_name:
                return entry
        return None
    
    @classmethod
    def _extract_from_clinic_website(cls, provider_name: str) -> Optional[Dict]:
        """Extract provider info from clinic website HTML."""
        html_content = cls._load_html(cls.CLINIC_PATH)
        
        if not html_content:
            return None
        
        # Simple HTML parsing for clinic info
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for provider sections
            normalized_name = cls._normalize_name(provider_name)
            
            # Extract clinic data (this is simplified - adapt based on actual HTML structure)
            clinic_info = {
                "name": provider_name,
                "phone": None,
                "address": None,
                "specialty": None
            }
            
            # Parse based on HTML structure
            for div in soup.find_all('div', class_='provider'):
                if normalized_name in cls._normalize_name(div.get_text()):
                    # Extract phone, address, specialty
                    phone_elem = div.find('span', class_='phone')
                    if phone_elem:
                        clinic_info["phone"] = phone_elem.get_text().strip()
                    
                    address_elem = div.find('span', class_='address')
                    if address_elem:
                        clinic_info["address"] = address_elem.get_text().strip()
                    
                    specialty_elem = div.find('span', class_='specialty')
                    if specialty_elem:
                        clinic_info["specialty"] = specialty_elem.get_text().strip()
                    
                    return clinic_info if any(clinic_info.values()) else None
        except Exception as e:
            print(f"Error parsing clinic website: {e}")
        
        return None
    
    @classmethod
    def validate_provider(cls, provider: ProviderInput) -> ValidationResult:
        """
        Validate a single provider against all data sources.
        Returns comprehensive validation result with confidence scores.
        """
        start_time = time.time()
        provider_id = str(uuid.uuid4())
        
        # Search all data sources
        npi_match = cls._search_npi_registry(provider.provider_name, provider.phone)
        license_match = cls._search_license_registry(provider.provider_name, provider.license_no)
        hospital_match = cls._search_hospital_roster(provider.provider_name)
        maps_match = cls._search_maps_listing(provider.provider_name)
        clinic_match = cls._extract_from_clinic_website(provider.provider_name)
        
        # Track sources
        sources_checked = ["npi", "license", "hospital", "maps", "clinic"]
        sources_matched = []
        
        if npi_match:
            sources_matched.append("npi")
        if license_match:
            sources_matched.append("license")
        if hospital_match:
            sources_matched.append("hospital")
        if maps_match:
            sources_matched.append("maps")
        if clinic_match:
            sources_matched.append("clinic")
        
        # Calculate confidence scores
        match_score = len(sources_matched) / len(sources_checked)
        
        # License confidence
        license_confidence = 0.0
        license_info = None
        if license_match:
            license_info = LicenseInfo(
                license_number=license_match.get("license_number"),
                status=license_match.get("status"),
                specialty=license_match.get("specialty"),
                expiration_date=license_match.get("expiration_date"),
                issuing_body=license_match.get("issuing_body")
            )
            license_confidence = 1.0 if license_match.get("status") == "Active" else 0.5
        
        # Location confidence
        location_confidence = 0.0
        verified_phone = None
        verified_address = None
        
        if npi_match and clinic_match:
            if npi_match.get("phone") == clinic_match.get("phone"):
                location_confidence += 0.5
                verified_phone = npi_match.get("phone")
            if npi_match.get("address") and clinic_match.get("address"):
                if npi_match.get("address").lower() in clinic_match.get("address", "").lower():
                    location_confidence += 0.5
                    verified_address = clinic_match.get("address")
        elif npi_match:
            location_confidence = 0.5
            verified_phone = npi_match.get("phone")
            verified_address = npi_match.get("address")
        
        # Hospital affiliation
        hospital_affiliation = None
        affiliation_confidence = 0.0
        if hospital_match:
            hospital_affiliation = HospitalAffiliation(
                hospital_name=hospital_match.get("hospital_name"),
                department=hospital_match.get("department"),
                position=hospital_match.get("position")
            )
            affiliation_confidence = 1.0
        
        # Specialty verification
        specialty_confidence = 0.0
        verified_specialty = None
        if clinic_match and clinic_match.get("specialty"):
            verified_specialty = clinic_match.get("specialty")
            specialty_confidence = 1.0
        elif license_match and license_match.get("specialty"):
            verified_specialty = license_match.get("specialty")
            specialty_confidence = 0.8
        
        # Calculate overall confidence
        confidence_scores = ConfidenceScores(
            identity_match=match_score,
            license_validity=license_confidence,
            location_verified=min(location_confidence, 1.0),
            hospital_affiliation=affiliation_confidence,
            specialty_verified=specialty_confidence,
            overall_confidence=(match_score + license_confidence + min(location_confidence, 1.0) + affiliation_confidence + specialty_confidence) / 5.0
        )
        
        # Determine validation status and issues
        validation_status = "UNVERIFIED"
        issues: List[ValidationIssue] = []
        risk_flags: List[RiskFlag] = []
        
        if len(sources_matched) >= 3:
            validation_status = "VERIFIED"
        elif len(sources_matched) >= 2:
            validation_status = "PARTIALLY_VERIFIED"
        
        # Check for issues
        if not license_match:
            issues.append(ValidationIssue(
                issue="No license found",
                severity="HIGH",
                source="license_registry",
                recommendation="Contact licensing board for verification"
            ))
        elif license_match.get("status") != "Active":
            issues.append(ValidationIssue(
                issue=f"License status is {license_match.get('status')}",
                severity="CRITICAL",
                source="license_registry",
                recommendation="Provider license may be invalid or expired"
            ))
            risk_flags.append(RiskFlag(
                flag="INACTIVE_LICENSE",
                severity="CRITICAL",
                description="Provider's license is not active"
            ))
            validation_status = "FLAGGED"
        
        if location_confidence < 0.5:
            issues.append(ValidationIssue(
                issue="Location information could not be verified",
                severity="MEDIUM",
                source="maps_listing",
                recommendation="Contact provider for address verification"
            ))
        
        if not hospital_match:
            issues.append(ValidationIssue(
                issue="No hospital affiliation found",
                severity="LOW",
                source="hospital_roster",
                recommendation="Verify hospital affiliation directly"
            ))
        
        # Determine next steps
        next_steps = []
        requires_manual_review = False
        requires_contact_verification = False
        
        if validation_status == "FLAGGED":
            requires_manual_review = True
            next_steps.append("Manual review required due to license issues")
        elif validation_status == "UNVERIFIED":
            requires_contact_verification = True
            next_steps.append("Contact provider for identity verification")
        elif len(sources_matched) < 3:
            requires_contact_verification = True
            next_steps.append("Additional verification recommended")
        
        processing_time_ms = (time.time() - start_time) * 1000
        
        return ValidationResult(
            provider_id=provider_id,
            input_data=provider.model_dump(),
            provider_name=provider.provider_name,
            npi_number=npi_match.get("npi") if npi_match else None,
            verified_phone=verified_phone,
            verified_address=verified_address,
            verified_specialty=verified_specialty,
            license_info=license_info,
            hospital_affiliation=hospital_affiliation,
            confidence_scores=confidence_scores,
            sources_checked=sources_checked,
            sources_matched=sources_matched,
            validation_status=validation_status,
            issues=issues,
            risk_flags=risk_flags,
            requires_manual_review=requires_manual_review,
            requires_contact_verification=requires_contact_verification,
            next_steps=next_steps,
            processing_time_ms=processing_time_ms
        )
    
    @classmethod
    async def validate_batch(cls, providers: List[ProviderInput], batch_id: str) -> BatchValidationResponse:
        """
        Validate multiple providers asynchronously.
        Returns batch response with all results.
        """
        batch_response = BatchValidationResponse(
            batch_id=batch_id,
            status="PROCESSING",
            total_providers=len(providers),
            started_at=datetime.utcnow()
        )
        
        cls.batch_jobs[batch_id] = batch_response
        
        start_time = time.time()
        results = []
        failed = 0
        
        # Validate providers
        for provider in providers:
            try:
                result = cls.validate_provider(provider)
                results.append(result)
            except Exception as e:
                print(f"Error validating provider {provider.provider_name}: {e}")
                failed += 1
        
        batch_response.results = results
        batch_response.completed = len(providers) - failed
        batch_response.failed = failed
        batch_response.status = "COMPLETED"
        batch_response.completed_at = datetime.utcnow()
        batch_response.processing_time_ms = (time.time() - start_time) * 1000
        
        cls.batch_jobs[batch_id] = batch_response
        return batch_response
    
    @classmethod
    def get_batch_status(cls, batch_id: str) -> Optional[BatchValidationResponse]:
        """Get the status of a batch validation job."""
        return cls.batch_jobs.get(batch_id)
