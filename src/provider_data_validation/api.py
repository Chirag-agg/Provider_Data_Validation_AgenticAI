"""
FastAPI application for Provider Data Validation System.
Main entry point for the API server.
"""

import os
import uuid
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio

from .models import (
    ProviderInput, ValidationResult, BatchValidationRequest, BatchValidationResponse,
    SingleValidationResponse, FileUploadResponse, HealthCheckResponse, 
    ErrorResponse, ValidationStatsResponse
)
from .services import ValidationService
from .file_processor import FileProcessor

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
    except Exception as e:
        return FileUploadResponse(
            file_id="",
            filename=file.filename,
            file_type=FileProcessor.get_file_type(file.filename),
            providers_extracted=0,
            extraction_status="error",
            extracted_providers=[]
        )


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
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            code="HTTP_ERROR",
            details={"path": str(request.url.path)}
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=str(exc),
            code="INTERNAL_ERROR",
            details={"path": str(request.url.path)}
        ).model_dump()
    )


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
            "get_provider": "GET /validate/{provider_id}"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=True
    )
