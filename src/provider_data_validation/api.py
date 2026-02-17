"""
FastAPI application for Provider Data Validation System.
Main entry point for the API server.
"""

import os
import uuid
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Request, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio

from .config import settings
from .logger import logger

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

# Add CORS middleware (use FRONTEND_URL or configured origins)
cors_origins = [
    "http://localhost:5173",      # Vite default dev server
    "http://localhost:5174",      # Alternative Vite port
    "http://localhost:3000",      # Alternative frontend port
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:3000",
    "http://localhost:8000",       # Same origin
]

if settings.FRONTEND_URL:
    cors_origins.append(settings.FRONTEND_URL)

if settings.CORS_ORIGINS:
    cors_origins.extend([o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()])

# Remove duplicates
cors_origins = list(set(cors_origins))

logger.info(f"CORS origins configured: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Store for file uploads
uploaded_files: dict = {}


# ==================== Health & Status ====================

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Check API health status."""
    # Best-effort: check Ollama availability
    if not settings.ENABLE_LLM:
        ollama_status = "disabled"
    else:
        ollama_status = "unknown"
        try:
            import httpx
            resp = httpx.get(settings.OLLAMA_BASE_URL + "/api/tags", timeout=2)
            ollama_status = "operational" if resp.status_code == 200 else "unavailable"
        except Exception:
            ollama_status = "unavailable"

    return HealthCheckResponse(
        status="healthy",
        components={
            "api": "operational",
            "validation_service": "operational",
            "file_processor": "operational",
            "ollama": ollama_status
        },
        system_info={
            "workers": 1,
            "queued_jobs": ValidationService.get_batch_count() if hasattr(ValidationService, 'get_batch_count') else 0
        }
    )


@app.get("/stats", response_model=ValidationStatsResponse)
async def get_stats():
    """Get validation statistics."""
    all_results = []
    batches = []
    if hasattr(ValidationService, 'get_all_results'):
        batches = ValidationService.get_all_results()
    else:
        try:
            batches = list(ValidationService.batch_jobs.values())
        except Exception:
            batches = []

    for batch in batches:
        # batch may be a dict (from Redis) or a model
        results = batch.get('results') if isinstance(batch, dict) else getattr(batch, 'results', [])
        if results:
            all_results.extend(results)

    total = len(all_results)

    def _status_of(r):
        return r.get('validation_status') if isinstance(r, dict) else getattr(r, 'validation_status', None)

    def _issues_of(r):
        return r.get('issues', []) if isinstance(r, dict) else getattr(r, 'issues', [])

    def _confidence_of(r):
        if isinstance(r, dict):
            cs = r.get('confidence_scores', {})
            return cs.get('overall_confidence', 0)
        else:
            return getattr(getattr(r, 'confidence_scores', None), 'overall_confidence', 0)

    successful = sum(1 for r in all_results if _status_of(r) in ["VERIFIED", "PARTIALLY_VERIFIED"])
    failed = sum(1 for r in all_results if _status_of(r) in ["UNVERIFIED", "FLAGGED"])

    issues_count = {}
    for result in all_results:
        for issue in _issues_of(result):
            key = issue.get('issue') if isinstance(issue, dict) else getattr(issue, 'issue', None)
            if not key:
                continue
            issues_count[key] = issues_count.get(key, 0) + 1

    most_common_issues = sorted(issues_count.items(), key=lambda x: x[1], reverse=True)[:5]
    most_common_issues = [issue for issue, count in most_common_issues]

    avg_conf = sum(_confidence_of(r) for r in all_results) / total if total > 0 else 0

    return ValidationStatsResponse(
        total_validations=total,
        successful=successful,
        failed=failed,
        success_rate=successful / total if total > 0 else 0,
        average_confidence=avg_conf,
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
    priority: str = Query("normal")
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
        if not settings.ENABLE_LLM:
            raise HTTPException(status_code=503, detail="LLM features disabled in this deployment")
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
            # Best-effort: load persisted batches if available
            batches = ValidationService.get_all_results() if hasattr(ValidationService, 'get_all_results') else list(ValidationService.batch_jobs.values())
            for batch in batches:
                results = batch.get('results') if isinstance(batch, dict) else getattr(batch, 'results', [])
                for result in results:
                    rid = result.get('provider_id') if isinstance(result, dict) else getattr(result, 'provider_id', None)
                    if rid == request.provider_id:
                        # Extract issues and discrepancies from validation
                        issues = result.get('issues') if isinstance(result, dict) else getattr(result, 'issues', [])
                        validation_data = {
                            'issues': [i.get('issue') if isinstance(i, dict) else getattr(i, 'issue', '') for i in issues] if issues else [],
                            'discrepancies': {},
                        }
                        # Check for phone mismatch
                        input_phone = result.get('input_data', {}).get('phone') if isinstance(result, dict) else result.input_data.get('phone')
                        verified_phone = result.get('verified_phone') if isinstance(result, dict) else getattr(result, 'verified_phone', None)
                        if input_phone != verified_phone:
                            validation_data['discrepancies']['phone'] = {
                                'old_value': input_phone or '',
                                'new_value': verified_phone or ''
                            }
                        # Check for specialty mismatch
                        input_spec = result.get('input_data', {}).get('specialty') if isinstance(result, dict) else result.input_data.get('specialty')
                        verified_spec = result.get('verified_specialty') if isinstance(result, dict) else getattr(result, 'verified_specialty', None)
                        if input_spec != verified_spec:
                            validation_data['discrepancies']['specialty'] = {
                                'old_value': input_spec or '',
                                'new_value': verified_spec or ''
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

        # If Twilio auth token is configured, validate signature
        try:
            signature = request.headers.get('X-Twilio-Signature') or request.headers.get('x-twilio-signature')
            if settings.TWILIO_AUTH_TOKEN and signature:
                from twilio.request_validator import RequestValidator
                validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
                # FastAPI request.url contains the full URL
                valid = validator.validate(str(request.url), dict(form_data), signature)
                if not valid:
                    raise HTTPException(status_code=403, detail="Invalid Twilio signature")
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Twilio signature validation skipped/failed: {e}")

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
            all_sessions = verification_store.get_all_sessions()
            for sid, sess in all_sessions.items():
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
            # verification_store.update_session accepts a session dict or model
            verification_store.update_session(existing_session)
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
            
            # Store using verification_store API
            verification_store.create_session(simple_session)
            
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


# ==================== Compliance Intelligence ====================

@app.get("/compliance/ingest")
async def ingest_sanctions():
    """Trigger sanction registry ingestion from OIG and SAM.gov."""
    try:
        from .compliance.sanction_ingestion import ingest_sanctions as run_ingest
        result = await run_ingest()
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.get("/compliance/check/{provider_id}")
async def check_provider_compliance(provider_id: str):
    """Get compliance status for a specific provider. Auto-calculates if not found."""
    try:
        status = ValidationService.get_provider_compliance_status(provider_id)
        if status:
            return {"success": True, "data": status}
        
        # If not found, return empty state with instructions
        return {
            "success": True, 
            "data": {
                "provider_id": provider_id,
                "cri_score": 0,
                "risk_level": "UNKNOWN",
                "risk_color": "gray",
                "factors": [],
                "sanction_matches": [],
                "calculated_at": None,
                "message": "Compliance status not yet calculated. Use POST /compliance/recalculate/{provider_id} to calculate."
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compliance/recalculate/{provider_id}")
async def recalculate_compliance(provider_id: str, provider_data: Optional[dict] = Body(None)):
    """Recalculate compliance risk for a provider. Accepts optional provider data."""
    try:
        # If no provider data provided, create minimal dataset
        if not provider_data:
            provider_data = {
                "id": provider_id,
                "full_name": "Unknown Provider",
                "npi": "",
                "license": "",
                "board_certified": False
            }
        else:
            provider_data["id"] = provider_id
        
        result = ValidationService.recalculate_provider_compliance(provider_id, provider_data)
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Compliance recalculation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Recalculation failed: {str(e)}")


@app.get("/compliance/sanctions/search")
async def search_sanctions(name: str, threshold: int = 80):
    """Search sanction registry for a provider name."""
    try:
        from .compliance.sanction_checker import check_sanctions
        matches = check_sanctions(name, threshold)
        return {"success": True, "matches": matches}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
            "drift_monitor": "POST /drift-monitor",
            "compliance_ingest": "GET /compliance/ingest",
            "compliance_check": "GET /compliance/check/{provider_id}",
            "compliance_recalculate": "POST /compliance/recalculate/{provider_id}",
            "sanctions_search": "GET /compliance/sanctions/search"
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
