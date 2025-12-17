"""
FastAPI application for Provider Data Validation System.
Main entry point for the API server.
"""

import os
import uuid
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio

from .models import (
    ProviderInput, ValidationResult, BatchValidationRequest, BatchValidationResponse,
    SingleValidationResponse, FileUploadResponse, HealthCheckResponse, 
    ErrorResponse, ValidationStatsResponse, VerificationRequest
)
from .services import ValidationService
from .tools.file_processor import FileProcessor

# Create FastAPI app
app = FastAPI(
    title="Provider Data Validation System",
    description="AI-powered provider verification across multiple data sources",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store for file uploads
uploaded_files: dict = {}


# ==================== Health & Status ====================

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Check API health status."""
    return HealthCheckResponse(
        status="healthy",
        components={
            "api": "operational",
            "validation_service": "operational",
            "file_processor": "operational"
        },
        system_info={
            "workers": 1,
            "queued_jobs": len(ValidationService.batch_jobs)
        }
    )


@app.get("/stats", response_model=ValidationStatsResponse)
async def get_stats():
    """Get validation statistics."""
    all_results = []
    for batch in ValidationService.batch_jobs.values():
        all_results.extend(batch.results)
    
    total = len(all_results)
    successful = sum(1 for r in all_results if r.validation_status in ["VERIFIED", "PARTIALLY_VERIFIED"])
    failed = sum(1 for r in all_results if r.validation_status in ["UNVERIFIED", "FLAGGED"])
    
    # Collect common issues
    issues_count = {}
    for result in all_results:
        for issue in result.issues:
            issues_count[issue.issue] = issues_count.get(issue.issue, 0) + 1
    
    most_common_issues = sorted(issues_count.items(), key=lambda x: x[1], reverse=True)[:5]
    most_common_issues = [issue for issue, count in most_common_issues]
    
    return ValidationStatsResponse(
        total_validations=total,
        successful=successful,
        failed=failed,
        success_rate=successful / total if total > 0 else 0,
        average_confidence=sum(r.confidence_scores.overall_confidence for r in all_results) / total if total > 0 else 0,
        most_common_issues=most_common_issues
    )


# ==================== Single Provider Validation ====================

@app.post("/validate", response_model=SingleValidationResponse)
async def validate_provider(provider: ProviderInput):
    """
    Validate a single provider.
    
    Returns comprehensive validation result with confidence scores.
    """
    try:
        result = ValidationService.validate_provider(provider)
        return SingleValidationResponse(
            success=True,
            data=result,
            processing_time_ms=result.processing_time_ms
        )
    except Exception as e:
        return SingleValidationResponse(
            success=False,
            error=str(e),
            processing_time_ms=0
        )


@app.post("/validate/batch", response_model=BatchValidationResponse)
async def validate_batch(
    request: BatchValidationRequest,
    background_tasks: BackgroundTasks
):
    """
    Validate multiple providers in batch.
    
    Returns batch job ID immediately. Use /batch/{batch_id} to check status.
    """
    batch_id = str(uuid.uuid4())
    
    # Queue background task
    background_tasks.add_task(
        ValidationService.validate_batch,
        request.providers,
        batch_id
    )
    
    # Return queued response
    return BatchValidationResponse(
        batch_id=batch_id,
        status="QUEUED",
        total_providers=len(request.providers)
    )


@app.get("/batch/{batch_id}", response_model=BatchValidationResponse)
async def get_batch_status(batch_id: str):
    """Get status of a batch validation job."""
    batch = ValidationService.get_batch_status(batch_id)
    
    if not batch:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")
    
    return batch


# ==================== File Upload ====================

@app.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a provider list file (PDF or Excel).
    
    Extracts provider information and returns list of providers found.
    """
    try:
        # Validate file
        file_content = await file.read()
        file_type = FileProcessor.get_file_type(file.filename)
        
        if file_type == 'unknown':
            raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF or XLSX")
        
        if not FileProcessor.validate_file(file_content, file_type):
            raise HTTPException(status_code=400, detail="Invalid or corrupted file")
        
        # Extract providers
        if file_type == 'pdf':
            extracted_providers = FileProcessor.extract_from_pdf(file_content)
        else:  # xlsx
            extracted_providers = FileProcessor.extract_from_excel(file_content)
        
        # Convert to ProviderInput objects
        providers = []
        for provider_dict in extracted_providers:
            try:
                provider = ProviderInput(**provider_dict)
                providers.append(provider)
            except Exception as e:
                print(f"Skipping invalid provider: {e}")
                continue
        
        # Store file info
        file_id = str(uuid.uuid4())
        uploaded_files[file_id] = {
            "filename": file.filename,
            "file_type": file_type,
            "providers_count": len(providers),
            "providers": providers
        }
        
        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            file_type=file_type,
            providers_extracted=len(providers),
            extraction_status="success" if len(providers) > 0 else "no_providers_found",
            extracted_providers=providers
        )
        
    except HTTPException:
        raise
    except ImportError as e:
        # OCR dependencies not installed
        error_msg = str(e)
        if "pytesseract" in error_msg or "pdf2image" in error_msg:
            error_msg = "OCR libraries not installed. The PDF appears to be scanned/handwritten. Install Tesseract OCR from https://github.com/UB-Mannheim/tesseract/wiki"
        raise HTTPException(status_code=400, detail=error_msg)
    except ValueError as e:
        # OCR or extraction failed
        raise HTTPException(status_code=400, detail=f"File processing failed: {str(e)}")
    except Exception as e:
        # Generic error with details
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@app.post("/upload/{file_id}/validate")
async def validate_uploaded_file(
    file_id: str,
    background_tasks: BackgroundTasks,
    priority: str = "normal"
):
    """
    Validate all providers from an uploaded file.
    
    Returns batch job ID for tracking.
    """
    if file_id not in uploaded_files:
        raise HTTPException(status_code=404, detail=f"File {file_id} not found")
    
    file_info = uploaded_files[file_id]
    batch_id = str(uuid.uuid4())
    
    # Queue validation
    background_tasks.add_task(
        ValidationService.validate_batch,
        file_info["providers"],
        batch_id
    )
    
    return {
        "batch_id": batch_id,
        "status": "QUEUED",
        "total_providers": len(file_info["providers"]),
        "message": f"Batch validation started for {file_info['filename']}"
    }


# ==================== Provider Details ====================

@app.get("/validate/{provider_id}", response_model=ValidationResult)
async def get_provider_result(provider_id: str):
    """
    Get validation result for a specific provider.
    
    Searches through all batch results.
    """
    for batch in ValidationService.batch_jobs.values():
        for result in batch.results:
            if result.provider_id == provider_id:
                return result
    
    raise HTTPException(status_code=404, detail=f"Provider {provider_id} not found")


# ==================== Webhook/Notification Support ====================

@app.post("/webhook/test")
async def test_webhook(webhook_url: str):
    """
    Test webhook connectivity.
    """
    import httpx
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                webhook_url,
                json={"status": "webhook_test", "timestamp": str(__import__('datetime').datetime.utcnow())}
            )
            return {"webhook_status": "ok", "response_code": response.status_code}
    except Exception as e:
        return {"webhook_status": "error", "error": str(e)}


# ==================== Error Handlers ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    error_response = ErrorResponse(
        error=exc.detail,
        code="HTTP_ERROR",
        details={"path": str(request.url.path)}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json')
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    error_response = ErrorResponse(
        error=str(exc),
        code="INTERNAL_ERROR",
        details={"path": str(request.url.path)}
    )
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(mode='json')
    )


# ==================== Drift Monitoring ====================

@app.post("/drift-monitor")
async def monitor_drift(provider_name: str):
    """
    Monitor credential drift for a provider by comparing current vs historical data.
    """
    try:
        from .crews.drift_monitoring_crew import DriftMonitoringCrew
        
        # Create crew and pass provider_name as input
        crew = DriftMonitoringCrew()
        
        # Kickoff the crew with the provider name as input
        result = crew.crew().kickoff(inputs={"provider_name": provider_name})
        
        # Parse the result - crew returns a raw string
        import json
        import re
        
        # Convert result to string if it's not already
        result_str = str(result.raw) if hasattr(result, 'raw') else str(result)
        
        # Clean up the string
        # Remove markdown code fences
        result_str = re.sub(r'```json\s*|\s*```', '', result_str)
        # Replace double curly braces
        result_str = result_str.replace('{{', '{').replace('}}', '}')
        # Remove any leading/trailing whitespace
        result_str = result_str.strip()
        
        # Parse as JSON
        result_data = json.loads(result_str)
        
        return {
            "success": True,
            "data": result_data
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Drift monitoring failed: {str(e)}")


# ==================== Provider Verification ====================

@app.post("/verify/start")
async def start_provider_verification(request: VerificationRequest):
    """
    Start interactive SMS verification for a provider.
    Intelligently asks only about mismatched/problematic fields.
    """
    try:
        from .tools.verification_service import start_verification
        from .models import VerificationRequest, VerificationResponse
        
        # Try to get validation results for this provider to identify issues
        validation_data = None
        try:
            # Check if we have validation results for this provider
            for batch in ValidationService.batch_jobs.values():
                for result in batch.results:
                    if result.provider_id == request.provider_id:
                        # Extract issues and discrepancies from validation
                        validation_data = {
                            'issues': [issue.issue for issue in result.issues] if result.issues else [],
                            'discrepancies': {},
                        }
                        # Check for phone mismatch
                        if result.input_data.get('phone') != result.verified_phone:
                            validation_data['discrepancies']['phone'] = {
                                'old_value': result.input_data.get('phone', ''),
                                'new_value': result.verified_phone or ''
                            }
                        # Check for specialty mismatch
                        if result.input_data.get('specialty') != result.verified_specialty:
                            validation_data['discrepancies']['specialty'] = {
                                'old_value': result.input_data.get('specialty', ''),
                                'new_value': result.verified_specialty or ''
                            }
                        break
        except Exception as e:
            print(f"[VERIFY] Could not fetch validation data: {e}")
        
        # Merge validation data with request data
        request_data = {
            'specialty': request.specialty,
            'phone': request.phone,
            'address': request.address,
            'license_number': request.license_number,
            'hospital': request.hospital
        }
        if validation_data:
            request_data.update(validation_data)
        
        # Pass enriched data to verification service  
        success, message, session = start_verification(request, request_data)
        
        if success:
            return VerificationResponse(
                success=True,
                session_id=session.session_id,
                status=session.status,
                message=message
            )
        else:
            return VerificationResponse(
                success=False,
                session_id=session.session_id if session else None,
                status=session.status if session else None,
                message=message,
                error=message
            )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@app.post("/verify/webhook")
async def verification_sms_webhook(request: Request):
    """
    Twilio webhook endpoint for incoming SMS responses.
    Configure this URL in your Twilio console.
    """
    try:
        from .tools.verification_service import process_sms_response
        
        # Parse form data from Twilio webhook
        form_data = await request.form()
        from_phone = form_data.get("From", "")
        message_body = form_data.get("Body", "")
        
        if not from_phone or not message_body:
            raise HTTPException(status_code=400, detail="Missing From or Body in webhook")
        
        # Process the response
        success, message = process_sms_response(from_phone, message_body)
        
        # Return TwiML response (Twilio expects XML)
        from fastapi.responses import Response
        return Response(
            content=f"<?xml version='1.0' encoding='UTF-8'?><Response></Response>",
            media_type="application/xml"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Still return valid TwiML even on error
        from fastapi.responses import Response
        return Response(
            content=f"<?xml version='1.0' encoding='UTF-8'?><Response></Response>",
            media_type="application/xml"
        )


@app.get("/verify/{session_id}")
async def get_verification_status(session_id: str):
    """
    Get the status of a verification session.
    """
    from .tools import verification_store
    
    session = verification_store.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    return session


@app.get("/provider/{provider_id}/verifications")
async def get_provider_verifications(provider_id: str):
    """
    Get all verification sessions for a provider.
    """
    from .tools import verification_store
    
    sessions = verification_store.get_provider_sessions(provider_id)
    
    return {
        "provider_id": provider_id,
        "total_verifications": len(sessions),
        "sessions": sessions
    }


@app.post("/verify/omni-webhook")
async def omni_dimension_webhook(request: Request):
    """
    Receive call verification data from Omni Dimension.
    This webhook is called after each verification call completes.
    
    Configure this URL in Omni Dimension:
    https://your-ngrok-url.ngrok.io/verify/omni-webhook
    """
    try:
        # Parse incoming webhook data from Omni Dimension
        data = await request.json()
        
        print(f"\n[WEBHOOK] Received Omni Dimension webhook: {data.get('call_id')}")
        
        # Extract call information
        call_data = {
            "call_id": data.get("call_id"),
            "status": data.get("status", "completed"),
            "duration": data.get("duration"),
            "timestamp": data.get("timestamp"),
            "provider_phone": data.get("phone") or data.get("to"),
            
            # Call Summary
            "callSummary": data.get("call_summary") or data.get("summary"),
            
            # Full Conversation
            "fullConversation": data.get("full_conversation") or data.get("conversation", []),
            
            # Sentiment Analysis
            "sentimentAnalysis": {
                "overall": data.get("sentiment", {}).get("overall", "Positive"),
                "confidence": data.get("sentiment", {}).get("confidence", 85),
                "mood": data.get("sentiment", {}).get("mood", "Cooperative"),
                "keyEmotions": data.get("sentiment", {}).get("emotions", [])
            },
            
            # Extracted Information
            "extractedInformation": data.get("extracted_info") or data.get("extracted_information", {})
        }
        
        # Store in verification_store
        from .tools import verification_store
        
        # Find provider by phone number
        provider_phone = call_data["provider_phone"]
        provider_id = data.get("provider_id") or data.get("metadata", {}).get("provider_id")
        
        # Try to find existing session by provider_id or phone
        session_id = data.get("session_id")
        existing_session = None
        
        if not session_id:
            # Search for existing session by phone or provider_id
            for sid, sess in verification_store.verification_sessions.items():
                sess_phone = sess.get("phone", "")
                sess_provider = sess.get("provider_id", "")
                
                if provider_phone and provider_phone in sess_phone:
                    existing_session = sess
                    session_id = sid
                    print(f"[INFO] Found existing session by phone: {session_id}")
                    break
                elif provider_id and provider_id in sess_provider:
                    existing_session = sess
                    session_id = sid
                    print(f"[INFO] Found existing session by provider_id: {session_id}")
                    break
        
        # Update existing session or create new one
        if existing_session:
            # Update existing session
            existing_session["call_verification"] = call_data
            existing_session["status"] = "COMPLETED"
            verification_store.update_session(session_id, existing_session)
            print(f"[SUCCESS] Updated existing session {session_id} with call data")
        else:
            # Create new session directly as a dict
            import uuid
            from datetime import datetime
            
            session_id = str(uuid.uuid4())
            simple_session = {
                "session_id": session_id,
                "provider_id": provider_id or provider_phone or "unknown",
                "provider_name": data.get("provider_name", "Unknown Provider"),
                "phone": provider_phone or "N/A",
                "status": "COMPLETED",
                "created_at": datetime.utcnow().isoformat(),
                "call_verification": call_data
            }
            
            # Store directly in verification_sessions dict
            verification_store.verification_sessions[session_id] = simple_session
            if provider_phone:
                verification_store.phone_to_session[provider_phone] = session_id
            
            print(f"[SUCCESS] Created new session {session_id} with call data")
        
        return {
            "success": True,
            "message": "Call data received and stored",
            "session_id": session_id,
            "call_id": call_data["call_id"]
        }
        
    except Exception as e:
        print(f"[ERROR] Error processing Omni webhook: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/verify/call-data/{provider_id}")
async def get_call_verification(provider_id: str):
    """Get call verification data (Mocked for Demo)"""
    # DEMO MODE: Return hardcoded conversation
    import datetime
    return {
        "success": True,
        "call_verification": {
            "status": "completed",
            "duration": "1m 20s",
            "callId": "demo-call-123",
            "timestamp": datetime.datetime.now().isoformat(),
            "callSummary": "Verified provider details. Address updated to Indiranagar, Bangalore. Hospital affiliation updated to Apollo Hospital. Alternate phone number 7123456789 confirmed.",
            "fullConversation": [
                {"time": "00:00", "sender": "system", "message": "Hello, this is the automated credential verification assistant calling to confirm your professional practise details. May I confirm that I'm speaking with Doctor R of Meta?"},
                {"time": "00:05", "sender": "provider", "message": "Yes."},
                {"time": "00:08", "sender": "system", "message": "Great, thank you. We have detected an address mismatch in our data. Is your practise still at MG Rd Bangalore 560001?"},
                {"time": "00:15", "sender": "provider", "message": "No."},
                {"time": "00:18", "sender": "system", "message": "Could you please state the correct address for your practise?"},
                {"time": "00:25", "sender": "provider", "message": "Yes, it's Indiranagar, Bangalore."},
                {"time": "00:30", "sender": "system", "message": "Got it. Your verified address is Indiranagar, Bangalore. Our records show an affiliation with Fortis Hospital. Do you still practise there?"},
                {"time": "00:38", "sender": "provider", "message": "No."},
                {"time": "00:40", "sender": "system", "message": "Thanks for letting me know. Could you please share your updated hospital affiliation?"},
                {"time": "00:45", "sender": "provider", "message": "Yes, it's Apollo Hospital."},
                {"time": "00:50", "sender": "system", "message": "Noted Your updated hospital affiliation is Apollo Hospital. Is there an alternate phone number where administrative teams can reach you?"},
                {"time": "00:58", "sender": "provider", "message": "Yes."},
                {"time": "01:00", "sender": "system", "message": "Please provide the alternate phone number for confirmation."},
                {"time": "01:05", "sender": "provider", "message": "7123456789."},
                {"time": "01:10", "sender": "system", "message": "Just to confirm, the alternate phone number is 7123456789, right?"},
                {"time": "01:15", "sender": "provider", "message": "Yes."},
                {"time": "01:18", "sender": "system", "message": "Thank you. Your verification is now complete. Have a great day."}
            ],
            "sentimentAnalysis": {
                "overall": "Positive",
                "confidence": 92,
                "mood": "Cooperative",
                "keyEmotions": ["Professional", "Patient", "Clear"]
            },
            "extractedInformation": {
                "addressConfirmed": "Indiranagar, Bangalore",
                "hospitalUpdated": "Apollo Hospital",
                "verificationsCompleted": "3/3",
                "correctionsProvided": "2"
            }
        }
    }


# ==================== Root ====================

@app.get("/")
async def root():
    """API root with documentation links."""
    return {
        "name": "Provider Data Validation System",
        "version": "1.0.0",
        "status": "running",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        },
        "endpoints": {
            "health": "GET /health",
            "stats": "GET /stats",
            "validate_single": "POST /validate",
            "validate_batch": "POST /validate/batch",
            "batch_status": "GET /batch/{batch_id}",
            "upload_file": "POST /upload",
            "validate_file": "POST /upload/{file_id}/validate",
            "get_provider": "GET /validate/{provider_id}",
            "drift_monitor": "POST /drift-monitor"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "provider_data_validation.api:app",
        host=host,
        port=port,
        reload=True
    )
