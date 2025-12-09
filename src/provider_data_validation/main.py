#!/usr/bin/env python

import os
from crews.notification_crew import NotificationCrew
import dotenv

dotenv.load_dotenv()
from crews.data_intake_crew.data_intake_crew import ProviderIntakeCrew

def kickoff():
    to = os.getenv("NOTIFY_TO")
    action = os.getenv("NOTIFY_ACTION", "sms").lower()
    message = os.getenv("NOTIFY_MESSAGE")

    if not to:
        raise ValueError("NOTIFY_TO must be set (E.164 format).")

    crew = NotificationCrew().crew()

    if action == "sms":
        if not message:
            raise ValueError("NOTIFY_MESSAGE is required for SMS.")
        print(f"Sending SMS to {to} ...")
        result = crew.kickoff(inputs={"to": to, "message": message})

    elif action == "call":
        print(f"Calling provider at {to} ...")
        result = crew.kickoff(inputs={"to": to})

    else:
        raise ValueError("NOTIFY_ACTION must be 'sms' or 'call'.")

    print("Crew result:", result.raw)

def kickoff_data_intake_crew():
    inputs = {
        "provider_name": "   Dr Aarav   Mehta ",
        "phone": "8123456789",
        "address": "",
        "specialty": "",
        "license_no": "DL-2024-1901"
    }

    # Enable the PDF tool only if a pdf_path was provided.
    use_pdf_tool = "pdf_path" in inputs and bool(inputs["pdf_path"])
    crew = ProviderIntakeCrew(use_pdf_tool=use_pdf_tool).crew()

    result = crew.kickoff(inputs)
    clean_output = result.tasks_output[-1]

    print(clean_output)

def kickoff_data_validation_crew():
    from crews.data_validation_crew.data_validation_crew import DataValidationCrew, extract_provider_data, validate_provider_data
    import json

    provider_name = "Dr Aarav Mehta"
    
    # Direct extraction without relying on agent
    extracted_data = extract_provider_data(provider_name)
    print("[EXTRACTED DATA]")
    print(json.dumps(extracted_data, indent=2))
    
    # Programmatic validation (no LLM needed)
    validation_result = validate_provider_data(extracted_data)
    print("\n[VALIDATION RESULT]")
    print(json.dumps(validation_result, indent=2))
    
    return validation_result



if __name__ == "__main__":
    kickoff_data_validation_crew()
    
