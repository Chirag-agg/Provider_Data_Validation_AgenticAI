"""
Simple test for Drift Monitoring Crew
Run from project root with: python test_drift_simple.py
"""

import sys
sys.path.insert(0, 'src')

from provider_data_validation.crews.drift_monitoring_crew import DriftMonitoringCrew

print("=" * 60)
print("Testing Drift Monitoring Crew")
print("=" * 60)
print("\nProvider: Dr Shalini Rao")
print("\nExpected changes based on historical data (2025-11-01):")
print("  - License status: Active → Suspended")
print("  - Hospital affiliation: SkinGlow Clinic (still affiliated)")
print("\n" + "=" * 60 + "\n")

try:
    crew = DriftMonitoringCrew()
    print("✅ Crew created successfully\n")
    
    print("Running drift detection...")
    result = crew.crew().kickoff(inputs={"provider_name": "Dr Shalini Rao"})
    
    print("\n" + "=" * 60)
    print("RESULT:")
    print("=" * 60)
    print(result)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
