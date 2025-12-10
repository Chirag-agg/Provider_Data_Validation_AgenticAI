"""Quick test to verify fuzzy matching works"""
import sys
from pathlib import Path

# Add crew to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "provider_data_validation"))

from crews.data_validation_crew.data_validation_crew import extract_provider_data, _fuzzy_match_name, _clean_name_for_matching

print("Testing Fuzzy Name Matching\n" + "="*50)

# Test name cleaning
test_names = [
    "Dr Aarav Mehta",
    "Aarav Mehta",
    "Dr. Aarav Mehta",
    "AARAV MEHTA"
]

print("\n1. Name Cleaning Test:")
for name in test_names:
    cleaned = _clean_name_for_matching(name)
    print(f"   '{name}' → '{cleaned}'")

# Test fuzzy matching
print("\n2. Fuzzy Matching Test:")
test_cases = [
    ("Shalini Rao", "Dr Shalini Rao"),
    ("Aarav Mehta", "Dr Aarav Mehta"),
    ("Dr. Aarav", "Dr Aarav Mehta"),
    ("Ritu Sharma", "Dr Ritu Sharma")
]

from difflib import SequenceMatcher
for input_name, database_name in test_cases:
    cleaned_input = _clean_name_for_matching(input_name)
    cleaned_db = _clean_name_for_matching(database_name)
    ratio = SequenceMatcher(None, cleaned_input, cleaned_db).ratio()
    match = "✓ MATCH" if ratio >= 0.7 else "✗ NO MATCH"
    print(f"   '{input_name}' vs '{database_name}': {ratio:.2%} {match}")

# Test actual extraction
print("\n3. Provider Extraction Test:")
test_providers = ["Shalini Rao", "Aarav Mehta", "Ritu Sharma", "Vikram Singh"]
for provider_name in test_providers:
    try:
        print(f"\n   Testing: '{provider_name}'")
        result = extract_provider_data(provider_name)
        
        found_sources = []
        if result['npi']: found_sources.append('NPI')
        if result['license']: found_sources.append('License')
        if result['hospital']: found_sources.append('Hospital')
        if result['maps']: found_sources.append('Maps')
        if result['clinic']: found_sources.append('Clinic')
        
        if found_sources:
            print(f"   ✓ Found in: {', '.join(found_sources)}")
        else:
            print(f"   ✗ Not found in any source")
    except Exception as e:
        print(f"   ✗ Error: {e}")

print("\n" + "="*50)
print("Test Complete!")
