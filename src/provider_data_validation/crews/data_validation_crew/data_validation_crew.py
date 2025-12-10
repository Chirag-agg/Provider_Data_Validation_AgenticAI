from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import BaseTool
import json
import os
import bs4

# Mock data paths
NPI_PATH = r"C:\Users\caagg\OneDrive\Desktop\Coding\CrewAI\provider_data_validation\mock_data\npi_registry.json"
LICENSE_PATH = r"C:\Users\caagg\OneDrive\Desktop\Coding\CrewAI\provider_data_validation\mock_data\license_registry.json"
HOSPITAL_PATH = r"C:\Users\caagg\OneDrive\Desktop\Coding\CrewAI\provider_data_validation\mock_data\hospital_roster.json"
MAPS_PATH = r"C:\Users\caagg\OneDrive\Desktop\Coding\CrewAI\provider_data_validation\mock_data\maps_listing.json"
CLINIC_PATH = r"C:\Users\caagg\OneDrive\Desktop\Coding\CrewAI\provider_data_validation\mock_data\clinic_website.html"

# Helper function to validate extracted data and compute confidence scores
def validate_provider_data(extracted_data: dict) -> dict:
    """Compute confidence scores based on extracted data."""
    npi = extracted_data.get("npi", {})
    license_data = extracted_data.get("license", {})
    hospital = extracted_data.get("hospital", {})
    maps = extracted_data.get("maps", {})
    clinic = extracted_data.get("clinic", {})
    
    # Count how many sources have data
    sources_found = sum([bool(npi), bool(license_data), bool(hospital), bool(maps), bool(clinic)])
    matched_sources = []
    if npi: matched_sources.append("npi")
    if license_data: matched_sources.append("license")
    if hospital: matched_sources.append("hospital")
    if maps: matched_sources.append("maps")
    if clinic: matched_sources.append("clinic")
    
    # NEW: Compare data across sources for quality score
    data_consistency_score = 1.0
    discrepancies = []
    
    # Check phone consistency across sources
    phones = []
    if npi and npi.get("phone"): phones.append(("npi", npi["phone"].replace(" ", "").replace("-", "")))
    if maps and maps.get("phone"): phones.append(("maps", maps["phone"].replace(" ", "").replace("-", "")))
    if clinic and clinic.get("phone"): phones.append(("clinic", clinic["phone"].replace(" ", "").replace("-", "")))
    
    if len(phones) > 1:
        unique_phones = set(p[1] for p in phones)
        if len(unique_phones) > 1:
            data_consistency_score -= 0.2
            discrepancies.append(f"Phone mismatch: {phones}")
    
    # Check specialty consistency
    specialties = []
    if npi and npi.get("specialty"): specialties.append(("npi", npi["specialty"].lower()))
    if license_data and license_data.get("specialty"): specialties.append(("license", license_data["specialty"].lower()))
    if clinic and clinic.get("specialty"): specialties.append(("clinic", clinic["specialty"].lower()))
    
    if len(specialties) > 1:
        unique_specialties = set(s[1] for s in specialties)
        if len(unique_specialties) > 1:
            data_consistency_score -= 0.25
            discrepancies.append(f"Specialty mismatch: {specialties}")
    
    # Check address/location consistency
    locations = []
    if npi and npi.get("address"): locations.append(("npi", npi["address"].lower()))
    if maps and maps.get("address"): locations.append(("maps", maps["address"].lower()))
    if clinic and clinic.get("address"): locations.append(("clinic", clinic["address"].lower()))
    
    if len(locations) > 1:
        # Check if addresses share common parts (city/state)
        all_same = all(locations[0][1] in loc[1] or loc[1] in locations[0][1] for loc in locations)
        if not all_same:
            data_consistency_score -= 0.15
            discrepancies.append(f"Location mismatch")
    
    # Final match score combines source coverage AND data quality
    source_coverage = sources_found / 5.0
    match_score = source_coverage * max(data_consistency_score, 0.3)  # Min 30% even with issues
    
    # License confidence
    license_confidence = 1.0 if license_data and license_data.get("status") == "Active" else 0.5 if license_data else 0.0
    
    # Location confidence (verify phone and address consistency)
    location_confidence = 0.0
    input_phone = ""
    verified_phone = ""
    input_address = ""
    verified_address = ""
    needs_location_verification = False
    
    if npi:
        input_phone = npi.get("phone", "")
        input_address = npi.get("address", "")
    if clinic:
        verified_phone = clinic.get("phone", "")
        verified_address = clinic.get("address", "")
    
    if input_phone and verified_phone:
        # Normalize phone for comparison
        phone_match = input_phone.replace(" ", "") == verified_phone.replace(" ", "")
        location_confidence += 0.5 if phone_match else 0.25
    if input_address and verified_address:
        address_match = input_address.lower() in verified_address.lower() or verified_address.lower() in input_address.lower()
        location_confidence += 0.5 if address_match else 0.25
    
    if location_confidence < 0.5:
        needs_location_verification = True
    
    # Affiliation confidence
    affiliation_confidence = 0.0
    hospital_name = ""
    department = ""
    if hospital:
        hospital_name = hospital.get("hospital_name", "")
        department = hospital.get("department", "")
        affiliation_confidence = 1.0
    
    # Specialty confidence
    specialty_confidence = 0.0
    input_specialty = ""
    verified_specialty = ""
    if npi:
        input_specialty = npi.get("specialty", "")
    if clinic:
        verified_specialty = clinic.get("specialty", "")
    
    if input_specialty and verified_specialty:
        specialty_match = input_specialty.lower() == verified_specialty.lower()
        specialty_confidence = 1.0 if specialty_match else 0.7
    elif input_specialty or verified_specialty:
        specialty_confidence = 0.5
    
    # Overall validation confidence
    overall_confidence = (match_score + license_confidence + location_confidence + affiliation_confidence + specialty_confidence) / 5.0
    
    # Determine if contact verification is needed
    requires_contact_verification = sources_found < 3 or location_confidence < 0.7
    
    # Identify issues
    issues = []
    if not license_data:
        issues.append("No license data found")
    elif license_data.get("status") != "Active":
        issues.append(f"License status is {license_data.get('status')}")
    if not hospital:
        issues.append("No hospital affiliation found")
    if location_confidence < 0.7:
        issues.append("Location/phone verification needed")
    if specialty_confidence < 0.8:
        issues.append("Specialty mismatch detected")
    
    return {
        "identity": {
            "match_score": round(match_score, 2),
            "matched_sources": matched_sources
        },
        "license": {
            "license_no": license_data.get("license_no", ""),
            "status": license_data.get("status", ""),
            "valid_till": license_data.get("valid_till", ""),
            "confidence": round(license_confidence, 2)
        },
        "location": {
            "input_phone": input_phone,
            "verified_phone": verified_phone,
            "input_address": input_address,
            "verified_address": verified_address,
            "confidence": round(min(location_confidence, 1.0), 2),
            "needs_verification": needs_location_verification
        },
        "affiliation": {
            "hospital": hospital_name,
            "department": department,
            "confidence": round(affiliation_confidence, 2)
        },
        "specialty": {
            "input_specialty": input_specialty,
            "verified_specialty": verified_specialty,
            "confidence": round(specialty_confidence, 2)
        },
        "issues": issues,
        "overall_validation_confidence": round(overall_confidence, 2),
        "requires_contact_verification": requires_contact_verification
    }


def _clean_name_for_matching(name: str) -> str:
    """Remove titles and normalize name for better fuzzy matching."""
    import re
    # Remove common titles
    name = re.sub(r'\b(dr\.?|doctor|md|phd|do)\b', '', name, flags=re.IGNORECASE)
    # Remove extra whitespace and periods
    name = re.sub(r'\.', '', name)
    name = ' '.join(name.split())
    return name.strip().lower()


def _fuzzy_match_name(input_name: str, candidates: list[dict], name_field: str = "name", threshold: float = 0.7) -> dict | None:
    """
    Find best matching provider from candidates using fuzzy matching.
    
    Args:
        input_name: Name to search for
        candidates: List of provider dicts
        name_field: Field name containing the provider name
        threshold: Minimum similarity ratio (0.0-1.0)
    
    Returns:
        Best matching provider dict if similarity >= threshold, else None
    """
    from difflib import SequenceMatcher
    
    cleaned_input = _clean_name_for_matching(input_name)
    best_match = None
    best_ratio = 0.0
    
    for candidate in candidates:
        candidate_name = candidate.get(name_field, "")
        if not candidate_name:
            continue
            
        cleaned_candidate = _clean_name_for_matching(candidate_name)
        
        # Calculate similarity ratio
        ratio = SequenceMatcher(None, cleaned_input, cleaned_candidate).ratio()
        
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = candidate
    
    return best_match if best_ratio >= threshold else None


# Helper function to extract provider records
def extract_provider_data(provider_name: str) -> dict:
    """Extract provider data from all registries using fuzzy name matching."""
    
    # NPI - Use fuzzy matching
    npi_data = None
    with open(NPI_PATH, "r", encoding="utf-8") as f:
        providers = json.load(f)["providers"]
        npi_data = _fuzzy_match_name(provider_name, providers, "name")
    
    # License - Use fuzzy matching
    license_data = None
    with open(LICENSE_PATH, "r", encoding="utf-8") as f:
        licenses = json.load(f)["licenses"]
        license_data = _fuzzy_match_name(provider_name, licenses, "doctor_name")
    
    # Hospital - Use fuzzy matching
    hospital_data = None
    with open(HOSPITAL_PATH, "r", encoding="utf-8") as f:
        hospitals_json = json.load(f)["hospitals"]
        # Flatten doctors from all hospitals
        all_doctors = []
        for h in hospitals_json:
            for d in h["doctors"]:
                all_doctors.append({"hospital_name": h["hospital_name"], **d})
        
        hospital_data = _fuzzy_match_name(provider_name, all_doctors, "name")
    
    # Maps - Use fuzzy matching
    maps_data = None
    with open(MAPS_PATH, "r", encoding="utf-8") as f:
        listings = json.load(f)["listings"]
        maps_data = _fuzzy_match_name(provider_name, listings, "name")
    
    # Clinic Website - Use fuzzy matching
    clinic_data = None
    with open(CLINIC_PATH, "r", encoding="utf-8") as f:
        soup = bs4.BeautifulSoup(f.read(), "html.parser")
        # Extract all doctors
        all_clinic_doctors = []
        for div in soup.find_all("div", class_="doctor"):
            doc_name = div.find("h2").text.strip()
            details = {}
            for p in div.find_all("p"):
                try:
                    key, value = p.text.split(":", 1)
                    details[key.strip().lower()] = value.strip()
                except:
                    continue
            
            all_clinic_doctors.append({
                "name": doc_name,
                "specialty": details.get("specialty"),
                "phone": details.get("phone"),
                "address": details.get("address"),
                "license_no": details.get("license no")
            })
        
        clinic_data = _fuzzy_match_name(provider_name, all_clinic_doctors, "name")
    
    return {
        "npi": npi_data or {},
        "license": license_data or {},
        "hospital": hospital_data or {},
        "maps": maps_data or {},
        "clinic": clinic_data or {}
    }


# Extraction tool for agent
class ExtractProviderTool(BaseTool):
    name: str = "extract_provider_records"
    description: str = "Extract provider records from all registries with fuzzy name matching."
    
    def _run(self, provider_name: str) -> dict:
        return extract_provider_data(provider_name)


# -------------------------
# ✅ CREW (FIXED)
# -------------------------

@CrewBase
class DataValidationCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    ollama_llm = LLM(
        model="ollama/llama3.1:latest",
        base_url="http://localhost:11434",
        api_key="not-needed",
    )

    @agent
    def data_extraction_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["data_extraction_agent"],
            tools=[ExtractProviderTool()],
            llm=self.ollama_llm,
            verbose=True,
        )

    # ✅ AGENT 2 — DATA VALIDATOR
    @agent
    def data_validation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["data_validation_agent"],
            llm=self.ollama_llm,
            verbose=True,
        )

    # ✅ TASK 1 — LOAD DATA
    @task
    def data_extraction_task(self) -> Task:
        return Task(
            config=self.tasks_config["data_extraction_task"],
            agent=self.data_extraction_agent(),
        )

    # ✅ TASK 2 — VALIDATE PROVIDER
    @task
    def data_validation_task(self) -> Task:
        # Create custom description with the extracted data to guide the validation
        return Task(
            description=f"""
You will receive structured extracted data:

{{
  "npi": {{}},
  "license": {{}},
  "hospital": {{}},
  "maps": {{}},
  "clinic": {{}}
}}

You MUST compute and return ONLY valid JSON with these fields:
- identity.match_score (0.0-1.0)
- license.confidence (0.0-1.0)
- location.confidence (0.0-1.0) 
- affiliation.confidence (0.0-1.0)
- specialty.confidence (0.0-1.0)
- overall_validation_confidence (0.0-1.0)
- requires_contact_verification (true/false)

Return this exact JSON structure - no markdown, no explanations:
{{
  "identity": {{"match_score": 0.00, "matched_sources": []}},
  "license": {{"license_no": "", "status": "", "valid_till": "", "confidence": 0.00}},
  "location": {{"input_phone": "", "verified_phone": "", "input_address": "", "verified_address": "", "confidence": 0.00, "needs_verification": false}},
  "affiliation": {{"hospital": "", "department": "", "confidence": 0.00}},
  "specialty": {{"input_specialty": "", "verified_specialty": "", "confidence": 0.00}},
  "issues": [],
  "overall_validation_confidence": 0.00,
  "requires_contact_verification": false
}}
""",
            expected_output="Valid JSON with all required validation fields",
            agent=self.data_validation_agent(),
        )

    # ✅ CREW PIPELINE
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
