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
        Validate a single provider against all data sources using DataValidationCrew with Ollama.
        Returns comprehensive validation result with confidence scores.
        """
        start_time = time.time()
        provider_id = str(uuid.uuid4())
        
        # ============================================================
        # HYBRID APPROACH: Try Ollama crew first, fallback to helpers
        # ============================================================
        crew_failed = False
        
        # Run DataValidationCrew with Ollama
        try:
            from .crews.data_validation_crew.data_validation_crew import DataValidationCrew
            
            print(f"\n🤖 Attempting validation with Ollama crew...")
            
            # Create and run the crew with Ollama agents
            crew = DataValidationCrew()
            result = crew.crew().kickoff(inputs={"provider_name": provider.provider_name})
            
            # Parse the crew output
            import json
            import re
            
            # Extract JSON from crew result
            result_str = str(result.raw) if hasattr(result, 'raw') else str(result)
            result_str = re.sub(r'```json\s*|\s*```', '', result_str)
            result_str = result_str.strip()
            
            # Debug: Print what we got
            print(f"\n{'='*60}")
            print(f"CREW RESULT (first 500 chars):")
            print(f"{'='*60}")
            print(result_str[:500] if len(result_str) > 500 else result_str)
            print(f"{'='*60}\n")
            
            # Check if result is empty
            if not result_str:
                print("⚠️ Crew returned empty result, falling back to helpers...")
                crew_failed = True
            else:
                # Parse the validation data
                validation_result = json.loads(result_str)
                
                # Check if crew found any sources
                matched_sources = validation_result.get("identity", {}).get("matched_sources", [])
                if not matched_sources or len(matched_sources) == 0:
                    print(f"⚠️ Crew found 0 sources for {provider.provider_name}, falling back to helpers...")
                    crew_failed = True
                else:
                    print(f"✅ Crew found {len(matched_sources)} sources: {matched_sources}")
                    
        except Exception as e:
            print(f"⚠️ Crew execution failed: {e}")
            print("   Falling back to helper functions...")
            crew_failed = True
        
        # FALLBACK: Use helper functions (ALWAYS USED NOW)
        if crew_failed:
            from .crews.data_validation_crew.data_validation_crew import extract_provider_data, validate_provider_data
            
            print(f"🔧 Using helper functions for {provider.provider_name}...")
            extracted_data = extract_provider_data(provider.provider_name)
            validation_result = validate_provider_data(extracted_data)
            print(f"✅ Helper functions completed")
        
        # The crew output or helper output is now in validation_result
        # Extract information from validation_result
        license_data = validation_result.get("license", {})
        affiliation_data = validation_result.get("affiliation", {})
        location_data = validation_result.get("location", {})
        specialty_data = validation_result.get("specialty", {})
        
        # Extract verified information from validation output
        verified_phone = location_data.get("verified_phone")
        verified_address = location_data.get("verified_address")
        verified_specialty = specialty_data.get("verified_specialty")
        
        # Build confidence scores
        confidence_scores = ConfidenceScores(
            identity_match=validation_result.get("identity", {}).get("match_score", 0.0),
            license_validity=license_data.get("confidence", 0.0),
            contact_info_accuracy=location_data.get("confidence", 0.0),
            hospital_affiliation=affiliation_data.get("confidence", 0.0),
            specialty_verification=specialty_data.get("confidence", 0.0),
            data_freshness=0.9,  # Mock data is relatively fresh
            overall_confidence=validation_result.get("overall_validation_confidence", 0.0)
        )
        
        # Build license info
        license_info = None
        if license_data.get("license_no"):
            license_info = LicenseInfo(
                license_number=license_data.get("license_no"),
                status=license_data.get("status"),
                specialty=verified_specialty or specialty_data.get("input_specialty"),
                expiration_date=license_data.get("valid_till"),
                issuing_body=license_data.get("issued_by", "")
            )
        
        # Build hospital affiliation
        hospital_affiliation = None
        if affiliation_data.get("hospital"):
            hospital_affiliation = HospitalAffiliation(
                hospital_name=affiliation_data.get("hospital"),
                department=affiliation_data.get("department"),
                position=affiliation_data.get("designation", "")
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
            npi_number=None,  # Crew doesn't return NPI directly
            verified_phone=verified_phone,
            verified_address=verified_address,
            verified_specialty=verified_specialty,
            license_info=license_info,
            hospital_affiliation=hospital_affiliation,
            confidence_scores=confidence_scores,
            sources_checked=["npi", "license", "hospital", "maps", "clinic"],
            sources_matched=validation_result.get("identity", {}).get("matched_sources", []),
            validation_status=validation_status,
            issues=issues,
            risk_flags=[],
            requires_manual_review=validation_status == "FLAGGED",
            requires_contact_verification=validation_result.get("requires_contact_verification", False),
            next_steps=[],
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
