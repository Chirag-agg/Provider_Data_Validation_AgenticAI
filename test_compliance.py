"""
Quick test script for Compliance Intelligence Module
"""
import asyncio
from src.provider_data_validation.compliance.sanction_ingestion import ingest_sanctions
from src.provider_data_validation.compliance.sanction_checker import check_sanctions, check_provider
from src.provider_data_validation.compliance.compliance_engine import calculate_cri
from src.provider_data_validation.compliance_store import load_sanctions, load_statuses


async def test_compliance_module():
    print("=" * 60)
    print("Compliance Intelligence Module - Test Suite")
    print("=" * 60)
    
    # Test 1: Sanction Ingestion
    print("\n[1/5] Testing Sanction Ingestion...")
    try:
        result = await ingest_sanctions()
        print(f"✓ Ingestion successful!")
        print(f"  - OIG records: {result['oig_records']}")
        print(f"  - SAM records: {result['sam_records']}")
        print(f"  - Total: {result['total']}")
    except Exception as e:
        print(f"✗ Ingestion failed: {e}")
    
    # Test 2: Load Sanctions
    print("\n[2/5] Testing Sanction Storage...")
    try:
        sanctions = load_sanctions()
        print(f"✓ Loaded {len(sanctions)} sanctions from storage")
        if len(sanctions) > 0:
            print(f"  - Sample: {sanctions[0]['full_name']} ({sanctions[0]['source']})")
    except Exception as e:
        print(f"✗ Storage load failed: {e}")
    
    # Test 3: Fuzzy Matching
    print("\n[3/5] Testing Fuzzy Name Matching...")
    try:
        # Test with a common name (likely to have matches)
        matches = check_sanctions("John Smith", threshold=70)
        print(f"✓ Found {len(matches)} matches for 'John Smith'")
        if len(matches) > 0:
            print(f"  - Top match: {matches[0]['matched_name']} ({matches[0]['similarity_score']}% similar)")
    except Exception as e:
        print(f"✗ Fuzzy matching failed: {e}")
    
    # Test 4: Provider Compliance Check
    print("\n[4/5] Testing Provider Compliance Check...")
    try:
        test_provider = {
            "id": "test-001",
            "full_name": "Dr. John Smith",
            "first_name": "John",
            "last_name": "Smith",
            "npi": "1234567890",
            "license": "MD12345",
            "board_certified": True,
            "updated_at": "2024-01-01T00:00:00"
        }
        
        check_result = check_provider(test_provider)
        print(f"✓ Provider check completed")
        print(f"  - Has sanctions: {check_result['has_sanction']}")
        print(f"  - Matches found: {len(check_result['matches'])}")
    except Exception as e:
        print(f"✗ Provider check failed: {e}")
    
    # Test 5: CRI Calculation
    print("\n[5/5] Testing CRI Calculation...")
    try:
        cri_result = calculate_cri(test_provider)
        print(f"✓ CRI calculated successfully")
        print(f"  - CRI Score: {cri_result['cri_score']}")
        print(f"  - Risk Level: {cri_result['risk_level']}")
        print(f"  - Risk Color: {cri_result['risk_color']}")
        print(f"  - Factors: {len(cri_result['factors'])}")
        for factor in cri_result['factors']:
            print(f"    • {factor}")
    except Exception as e:
        print(f"✗ CRI calculation failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Suite Complete")
    print("=" * 60)
    
    # Check stored compliance statuses
    print("\n[Bonus] Checking Stored Compliance Data...")
    try:
        statuses = load_statuses()
        print(f"✓ Found {len(statuses)} stored compliance records")
        
        if len(statuses) > 0:
            print("\nRisk Distribution:")
            risk_counts = {}
            for status in statuses:
                level = status.get('risk_level', 'UNKNOWN')
                risk_counts[level] = risk_counts.get(level, 0) + 1
            
            for level, count in sorted(risk_counts.items()):
                print(f"  - {level}: {count}")
    except Exception as e:
        print(f"✗ Could not load statuses: {e}")


if __name__ == "__main__":
    asyncio.run(test_compliance_module())
