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
        Validate a single provider against all data sources using CrewAI.
        Returns comprehensive validation result with confidence scores.
        """
        start_time = time.time()
        provider_id = str(uuid.uuid4())
        
        # Import CrewAI validation functions
        try:
            import sys
            crew_path = cls.BASE_PATH / "src" / "provider_data_validation" / "crews" / "data_validation_crew"
            sys.path.insert(0, str(crew_path.parent.parent))
            
            from .crews.data_validation_crew.data_validation_crew import extract_provider_data, validate_provider_data
            
            # Extract data from all sources using just the provider name
            extracted_data = extract_provider_data(provider.provider_name)
            
            # Validate the extracted data
            validation_result = validate_provider_data(extracted_data)
            
            # Convert CrewAI result to our ValidationResult format
            npi_data = extracted_data.get("npi", {})
            license_data = extracted_data.get("license", {})
            hospital_data = extracted_data.get("hospital", {})
            maps_data = extracted_data.get("maps", {})
            clinic_data = extracted_data.get("clinic", {})
            
            # Extract verified information
            verified_phone = npi_data.get("phone") or maps_data.get("phone") or clinic_data.get("phone")
            verified_address = npi_data.get("address") or maps_data.get("address") or clinic_data.get("address")
            verified_specialty = npi_data.get("specialty") or clinic_data.get("specialty")
            
            # Build confidence scores
            confidence_scores = ConfidenceScores(
                identity_match=validation_result["identity"]["match_score"],
                license_validity=validation_result["license"]["confidence"],
                contact_info_accuracy=validation_result["location"]["confidence"],
                hospital_affiliation=validation_result["affiliation"]["confidence"],
                specialty_verification=validation_result["specialty"]["confidence"],
                data_freshness=0.9,  # Mock data is relatively fresh
                overall_confidence=validation_result["overall_validation_confidence"]
            )
            
            # Build license info
            license_info = None
            if license_data:
                license_info = LicenseInfo(
                    license_number=license_data.get("license_no"),
                    status=license_data.get("status"),
                    specialty=license_data.get("specialty"),
                    expiration_date=license_data.get("valid_till"),
                    issuing_body=license_data.get("issuing_authority")
                )
            
            # Build hospital affiliation
            hospital_affiliation = None
            if hospital_data:
                hospital_affiliation = HospitalAffiliation(
                    hospital_name=hospital_data.get("hospital_name"),
                    department=hospital_data.get("department"),
                    position=hospital_data.get("position")
                )
            
            # Determine validation status
            match_score = validation_result["identity"]["match_score"]
            if match_score >= 0.6:
                validation_status = "VERIFIED"
            elif match_score >= 0.4:
                validation_status = "PARTIALLY_VERIFIED"
            else:
                validation_status = "UNVERIFIED"
            
            # Check for critical issues
            if license_data and license_data.get("status") != "Active":
                validation_status = "FLAGGED"
            
            # Build issues list
            issues: List[ValidationIssue] = []
            for issue_text in validation_result.get("issues", []):
                severity = "HIGH" if "license" in issue_text.lower() else "MEDIUM"
                issues.append(ValidationIssue(
                    issue=issue_text,
                    severity=severity,
                    source="validation_crew",
                    recommendation="Review and verify manually"
                ))
            
            processing_time_ms = (time.time() - start_time) * 1000
            
            return ValidationResult(
                provider_id=provider_id,
                input_data=provider.model_dump(),
                provider_name=provider.provider_name,
                npi_number=npi_data.get("npi") if npi_data else None,
                verified_phone=verified_phone,
                verified_address=verified_address,
                verified_specialty=verified_specialty,
                license_info=license_info,
                hospital_affiliation=hospital_affiliation,
                confidence_scores=confidence_scores,
                sources_checked=["npi", "license", "hospital", "maps", "clinic"],
                sources_matched=validation_result["identity"]["matched_sources"],
                validation_status=validation_status,
                issues=issues,
                risk_flags=[],
                requires_manual_review=validation_status == "FLAGGED",
                requires_contact_verification=validation_result.get("requires_contact_verification", False),
                next_steps=[],
                processing_time_ms=processing_time_ms
            )
            
        except Exception as e:
            print(f"Error in CrewAI validation: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback to basic validation
            processing_time_ms = (time.time() - start_time) * 1000
            return ValidationResult(
                provider_id=provider_id,
                input_data=provider.model_dump(),
                provider_name=provider.provider_name,
                npi_number=None,
                verified_phone=None,
                verified_address=None,
                verified_specialty=None,
                license_info=None,
                hospital_affiliation=None,
                confidence_scores=ConfidenceScores(
                    identity_match=0.0,
                    license_validity=0.0,
                    contact_info_accuracy=0.0,
                    hospital_affiliation=0.0,
                    specialty_verification=0.0,
                    data_freshness=0.0,
                    overall_confidence=0.0
                ),
                sources_checked=["npi", "license", "hospital", "maps", "clinic"],
                sources_matched=[],
                validation_status="UNVERIFIED",
                issues=[ValidationIssue(
                    issue=f"Validation error: {str(e)}",
                    severity="CRITICAL",
                    source="system",
                    recommendation="Check system logs"
                )],
                risk_flags=[],
                requires_manual_review=True,
                requires_contact_verification=True,
                next_steps=["System error - manual review required"],
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
