from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import BaseTool
import json
import os
from datetime import datetime
from typing import Optional, Dict, List, Any

# Paths
HISTORICAL_DATA_DIR = r"C:\Users\caagg\OneDrive\Desktop\Coding\CrewAI\provider_data_validation\mock_data\historical"
LICENSE_PATH = r"C:\Users\caagg\OneDrive\Desktop\Coding\CrewAI\provider_data_validation\mock_data\license_registry.json"
HOSPITAL_PATH = r"C:\Users\caagg\OneDrive\Desktop\Coding\CrewAI\provider_data_validation\mock_data\hospital_roster.json"
NPI_PATH = r"C:\Users\caagg\OneDrive\Desktop\Coding\CrewAI\provider_data_validation\mock_data\npi_registry.json"
MAPS_PATH = r"C:\Users\caagg\OneDrive\Desktop\Coding\CrewAI\provider_data_validation\mock_data\maps_listing.json"


# Helper function to load historical data
def load_historical_data(provider_name: str) -> Optional[Dict[str, Any]]:
    """
    Load historical provider data from snapshot files.
    
    Args:
        provider_name: Name of the provider to search for
        
    Returns:
        Historical provider data dict or None if not found
    """
    # Find the most recent snapshot
    snapshot_files = []
    if os.path.exists(HISTORICAL_DATA_DIR):
        for filename in os.listdir(HISTORICAL_DATA_DIR):
            if filename.endswith('.json'):
                snapshot_files.append(os.path.join(HISTORICAL_DATA_DIR, filename))
    
    if not snapshot_files:
        return None
    
    # Use the most recent snapshot (by filename)
    snapshot_files.sort(reverse=True)
    latest_snapshot = snapshot_files[0]
    
    try:
        with open(latest_snapshot, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Find the provider in the snapshot
        for provider in data.get('providers', []):
            if provider.get('name', '').lower() == provider_name.lower():
                return provider
    except Exception as e:
        print(f"Error loading historical data: {e}")
    
    return None


# Helper function to load current provider data
def load_current_data(provider_name: str) -> Dict[str, Any]:
    """
    Load current provider data from all registries.
    
    Args:
        provider_name: Name of the provider to search for
        
    Returns:
        Dict with current data from all sources
    """
    current_data = {
        "license": {},
        "hospital": {},
        "npi": {},
        "maps": {}
    }
    
    # Load from license registry
    if os.path.exists(LICENSE_PATH):
        with open(LICENSE_PATH, 'r', encoding='utf-8') as f:
            license_data = json.load(f)
        for record in license_data.get('licenses', []):
            if record.get('doctor_name', '').lower() == provider_name.lower():
                current_data['license'] = record
                break
    
    # Load from hospital roster
    if os.path.exists(HOSPITAL_PATH):
        with open(HOSPITAL_PATH, 'r', encoding='utf-8') as f:
            hospital_data = json.load(f)
        for hospital in hospital_data.get('hospitals', []):
            for doctor in hospital.get('doctors', []):
                if doctor.get('name', '').lower() == provider_name.lower():
                    current_data['hospital'] = {
                        **doctor,
                        'hospital_name': hospital.get('hospital_name'),
                        'location': hospital.get('location')
                    }
                    break
    
    # Load from NPI registry
    if os.path.exists(NPI_PATH):
        with open(NPI_PATH, 'r', encoding='utf-8') as f:
            npi_data = json.load(f)
        for record in npi_data.get('providers', []):
            if record.get('name', '').lower() == provider_name.lower():
                current_data['npi'] = record
                break
    
    # Load from maps listing
    if os.path.exists(MAPS_PATH):
        with open(MAPS_PATH, 'r', encoding='utf-8') as f:
            maps_data = json.load(f)
        for record in maps_data.get('clinics', []):
            for doc in record.get('doctors', []):
                if doc.get('name', '').lower() == provider_name.lower():
                    current_data['maps'] = {
                        **doc,
                        'clinic_name': record.get('clinic_name'),
                        'clinic_address': record.get('address')
                    }
                    break
    
    return current_data


# Tool to load historical data
class HistoricalDataTool(BaseTool):
    name: str = "load_historical_provider_data"
    description: str = "Load historical snapshot data for a provider by name."
    
    def _run(self, provider_name: str) -> str:
        historical = load_historical_data(provider_name)
        if historical:
            return json.dumps(historical, indent=2)
        return json.dumps({"error": "No historical data found", "provider_name": provider_name})


# Tool to load current data
class CurrentDataTool(BaseTool):
    name: str = "load_current_provider_data"
    description: str = "Load current provider data from all registries."
    
    def _run(self, provider_name: str) -> str:
        current = load_current_data(provider_name)
        return json.dumps(current, indent=2)


# Tool to compare data and detect changes
class CompareDataTool(BaseTool):
    name: str = "compare_provider_data"
    description: str = "Compare current and historical provider data to detect changes."
    
    def _run(self, provider_name: str) -> str:
        """
        Compare current vs historical data and return detected changes.
        """
        historical = load_historical_data(provider_name)
        current = load_current_data(provider_name)
        
        if not historical:
            return json.dumps({
                "changes": [],
                "note": "No historical data available for comparison"
            })
        
        changes = []
        
        # Compare license status
        hist_license = historical.get('license', {})
        curr_license = current.get('license', {})
        
        if hist_license and curr_license:
            # Check license status
            if hist_license.get('status') != curr_license.get('status'):
                changes.append(
                    f"License status changed: {hist_license.get('status')} → {curr_license.get('status')}"
                )
            
            # Check specialty
            if hist_license.get('specialty') != curr_license.get('specialty'):
                changes.append(
                    f"Specialty changed: {hist_license.get('specialty')} → {curr_license.get('specialty')}"
                )
        
        # Compare contact information
        hist_contact = historical.get('contact', {})
        
        # Get current phone from any available source
        curr_phone = (current.get('license', {}).get('phone') or 
                     current.get('hospital', {}).get('phone') or
                     current.get('npi', {}).get('phone'))
        
        if hist_contact.get('phone') and curr_phone:
            # Normalize phone numbers for comparison
            hist_phone = hist_contact.get('phone').replace(' ', '').replace('-', '')
            curr_phone_norm = curr_phone.replace(' ', '').replace('-', '')
            if hist_phone != curr_phone_norm:
                changes.append(
                    f"Phone number updated: {hist_contact.get('phone')} → {curr_phone}"
                )
        
        # Compare address
        hist_address = hist_contact.get('address')
        curr_location = current.get('hospital', {}).get('location')
        
        if hist_address and curr_location:
            if hist_address.lower() != curr_location.lower():
                changes.append(
                    f"Address changed: {hist_address} → {curr_location}"
                )
        
        # Compare hospital affiliation
        hist_affiliation = historical.get('affiliation', {})
        curr_hospital = current.get('hospital', {})
        
        hist_hospital_name = hist_affiliation.get('hospital')
        curr_hospital_name = curr_hospital.get('hospital_name')
        
        if hist_hospital_name:
            if not curr_hospital_name:
                changes.append(f"Hospital affiliation removed: {hist_hospital_name}")
            elif hist_hospital_name != curr_hospital_name:
                changes.append(
                    f"Hospital affiliation changed: {hist_hospital_name} → {curr_hospital_name}"
                )
        
        return json.dumps({"changes": changes}, indent=2)


# -------------------------
# DRIFT MONITORING CREW
# -------------------------

@CrewBase
class DriftMonitoringCrew:
    """Provider Credential Drift Monitoring Crew"""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    ollama_llm = LLM(
        model="ollama/llama3.1:latest",
        base_url="http://localhost:11434",
        api_key="not-needed",
    )
    
    @agent
    def drift_detection_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['drift_detection_agent'],
            tools=[HistoricalDataTool(), CurrentDataTool(), CompareDataTool()],
            llm=self.ollama_llm,
        )
    
    @agent
    def risk_scoring_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['risk_scoring_agent'],
            llm=self.ollama_llm,
        )
    
    @task
    def drift_detection_task(self) -> Task:
        return Task(
            config=self.tasks_config['drift_detection_task'],
        )
    
    @task
    def risk_assessment_task(self) -> Task:
        return Task(
            config=self.tasks_config['risk_assessment_task'],
        )
    
    @crew
    def crew(self) -> Crew:
        """Creates the Drift Monitoring Crew"""
        return Crew(
            agents=self.agents,  # Auto-loaded by @agent decorators
            tasks=self.tasks,    # Auto-loaded by @task decorators
            process=Process.sequential,
            verbose=True,
        )
