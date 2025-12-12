"""
Test script for Drift Monitoring Crew
Tests the credential change detection functionality
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from provider_data_validation.crews.drift_monitoring_crew.drift_monitoring_crew import DriftMonitoringCrew

def test_drift_monitoring():
    """Test drift monitoring with Dr Shalini Rao"""
    print("=" * 60)
    print("Testing Drift Monitoring Crew")
    print("=" * 60)
    print("\nProvider: Dr Shalini Rao")
    print("\nExpected changes:")
    print("  - License status: Active → Suspended")
    print("  - Phone number: Should be missing in current hospital data")
    print("  - Hospital affiliation: SkinGlow Clinic (still present)")
    print("\n" + "=" * 60)
    
    try:
        crew = DriftMonitoringCrew()
        result = crew.crew().kickoff(inputs={"provider_name": "Dr Shalini Rao"})
        
        print("\n✅ Crew execution completed!")
        print("\nResult:")
        print(result)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_drift_monitoring()
