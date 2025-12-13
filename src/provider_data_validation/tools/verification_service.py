"""
Verification SMS service.
Handles sending verification messages and processing responses.
"""

import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from .models import VerificationSession, VerificationStatus, VerificationRequest
from . import verification_store


def format_verification_sms(provider_name: str, data: Dict[str, Any]) -> str:
    """Format the initial verification SMS message.
    Smart mode: Only asks about fields with issues/mismatches.
    """
    # Extract issues/mismatches if available
    issues = data.get('issues', [])
    discrepancies = data.get('discrepancies', {})
    
    # If there are specific issues, ask only about those
    if issues or discrepancies:
        message_parts = [f"Hi {provider_name},", ""]
        
        # Check discrepancies (SKIP: phone=delivery proves it, specialty=doesn't change)
        if discrepancies:
            if 'address' in discrepancies:
                old = discrepancies['address'].get('old_value', '')
                new = discrepancies['address'].get('new_value', '')
                message_parts.append(f"Address mismatch:")
                message_parts.append(f"A: {old}")
                message_parts.append(f"B: {new}")
                message_parts.append(f"Reply A or B.")
                return "\n".join(message_parts)
        
        # Ask about mutable fields only (address, hospital, etc.)
        if issues:
            # Filter to only ask about changeable information
            changeable_issues = [i for i in issues if 'specialty' not in i.lower() and 'phone' not in i.lower()]
            if changeable_issues:
                issue_text = changeable_issues[0] if isinstance(changeable_issues, list) else str(changeable_issues)
                message_parts.append(f"Issue: {issue_text[:50]}")
                message_parts.append("")
                message_parts.append("Reply YES if all correct or NO to update.")
                return "\n".join(message_parts)
    
    # Fallback: Ask about key fields only
    message_parts = [f"Hi {provider_name},", "", "Please confirm:"]
    
    if data.get("specialty"):
        message_parts.append(f"Specialty: {data['specialty']}")
    if data.get("phone"):
        message_parts.append(f"Phone: {data['phone']}")
    
    message_parts.append("")
    message_parts.append("Reply YES to confirm or NO to update.")
    
    return "\n".join(message_parts)


def format_correction_request_sms(provider_name: str) -> str:
    """Format the SMS requesting corrections."""
    return f"""Thank you {provider_name}.

Please reply with correct information.

Example: Specialty: Cardiology, Phone: +123456"""


def send_verification_sms(phone: str, message: str) -> Optional[str]:
    """
    Send SMS using Twilio.
    Returns message SID if successful, None otherwise.
    """
    try:
        print(f"[SMS] Attempting to send to: {phone}")
        print(f"[SMS] Message: {message[:100]}...")  # First 100 chars
        
        from .tools.twilio_tools import SendRealSMSTool
        
        tool = SendRealSMSTool()
        result = tool._run(to=phone, message=message)
        
        print(f"[SMS] Tool result: {result}")
        
        # Extract SID from result (format: "SMS sent: SM...")
        if "SMS sent:" in result:
            sid = result.split("SMS sent:")[1].strip()
            print(f"[SMS] Success! SID: {sid}")
            return sid
        else:
            print(f"[SMS] Warning: Unexpected result format: {result}")
            return None
    except Exception as e:
        print(f"[SMS] ERROR: Failed to send SMS: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_verification_session(request: VerificationRequest) -> VerificationSession:
    """Create a new verification session."""
    session_id = str(uuid.uuid4())
    
    original_data = {}
    if request.specialty:
        original_data["specialty"] = request.specialty
    if request.address:
        original_data["address"] = request.address
    if request.license_number:
        original_data["license_number"] = request.license_number
    if request.hospital:
        original_data["hospital"] = request.hospital
    # Always include phone even though we're sending TO it
    original_data["phone"] = request.phone
    
    session = VerificationSession(
        session_id=session_id,
        provider_id=request.provider_id,
        provider_name=request.provider_name,
        phone=request.phone,
        original_data=original_data,
        status=VerificationStatus.PENDING_RESPONSE,
    )
    
    verification_store.create_session(session)
    return session


def start_verification(request: VerificationRequest, enriched_data: Dict[str, Any] = None) -> tuple[bool, str, Optional[VerificationSession]]:
    """
    Start a verification workflow.
    Returns (success, message, session).
    
    Args:
        request: Verification request with provider details
        enriched_data: Optional dict with validation results (issues, discrepancies)
    """
    # Check if there's already an active session for this phone
    existing_session = verification_store.get_session_by_phone(request.phone)
    if existing_session and existing_session.status == VerificationStatus.PENDING_RESPONSE:
        return False, f"Active verification already in progress for this phone number", existing_session
    
    # Create new session
    session = create_verification_session(request)
    
    # Use enriched data if available, otherwise use request data
    data_for_sms = enriched_data if enriched_data else session.original_data
    
    # Format and send initial SMS (will be smart if enriched_data has issues/discrepancies)
    sms_message = format_verification_sms(request.provider_name, data_for_sms)
    sms_sid = send_verification_sms(request.phone, sms_message)
    
    if not sms_sid:
        session.status = VerificationStatus.FAILED
        verification_store.update_session(session)
        return False, "Failed to send verification SMS", session
    
    # Update session with SMS info
    session.sms_sid = sms_sid
    session.sms_count = 1
    verification_store.update_session(session)
    
    return True, "Verification SMS sent successfully", session


def process_sms_response(from_phone: str, message_body: str) -> tuple[bool, str]:
    """
    Process incoming SMS response.
    Returns (success, reply_message).
    """
    print(f"\n[WEBHOOK] Processing SMS response")
    print(f"[WEBHOOK] From: {from_phone}")
    print(f"[WEBHOOK] Message: {message_body[:100]}")
    
    # Find active session for this phone
    session = verification_store.get_session_by_phone(from_phone)
    
    if not session:
        print(f"[WEBHOOK] ERROR: No active session found for {from_phone}")
        print(f"[WEBHOOK] Checking all sessions...")
        all_sessions = verification_store.get_all_sessions()
        print(f"[WEBHOOK] Total sessions in store: {len(all_sessions)}")
        for s in all_sessions:
            print(f"[WEBHOOK]   Session {s.session_id[:8]}... - Phone: {s.phone} - Status: {s.status}")
        return False, "No active verification found for this number."
    
    print(f"[WEBHOOK] Found session: {session.session_id}")
    print(f"[WEBHOOK] Current status: {session.status}")
    
    if not session:
        return False, "No active verification found for this number."
    
    # Normalize message
    message_body = message_body.strip().upper()
    
    # Handle based on current status
    if session.status == VerificationStatus.PENDING_RESPONSE:
        # Awaiting YES/NO
        if "YES" in message_body or "Y" == message_body:
            # Confirmed
            session.initial_response = "YES"
            session.status = VerificationStatus.CONFIRMED
            session.responded_at = datetime.utcnow()
            session.completed_at = datetime.utcnow()
            verification_store.update_session(session)
            
            reply = f"Thank you for confirming, {session.provider_name}! Your information is verified."
            send_verification_sms(from_phone, reply)
            return True, "Verification confirmed"
            
        elif "NO" in message_body or "N" == message_body:
            # Needs corrections
            session.initial_response = "NO"
            session.status = VerificationStatus.CORRECTIONS_NEEDED
            session.responded_at = datetime.utcnow()
            verification_store.update_session(session)
            
            # Ask for corrections
            correction_request = format_correction_request_sms(session.provider_name)
            sms_sid = send_verification_sms(from_phone, correction_request)
            session.sms_count += 1
            verification_store.update_session(session)
            
            return True, "Awaiting corrections"
        else:
            # Invalid response
            reply = f"Please reply with YES to confirm or NO if corrections are needed."
            send_verification_sms(from_phone, reply)
            return False, "Invalid response, prompted for YES/NO"
    
    elif session.status == VerificationStatus.CORRECTIONS_NEEDED:
        # Receiving corrections
        session.correction_text = message_body
        session.status = VerificationStatus.COMPLETED
        session.completed_at = datetime.utcnow()
        verification_store.update_session(session)
        
        reply = f"Thank you, {session.provider_name}! We've received your corrections and will update our records."
        send_verification_sms(from_phone, reply)
        return True, "Corrections received"
    
    else:
        # Session already completed/closed
        return False, "This verification session has already been completed."
