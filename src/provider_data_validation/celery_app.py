from .config import settings
from celery import Celery
from .logger import logger


# Create a simple Celery app using Redis as broker/backend when available.
broker = settings.REDIS_URL or "redis://localhost:6379/0"
backend = settings.REDIS_URL or "redis://localhost:6379/1"

celery = Celery("provider_validation", broker=broker, backend=backend)
celery.conf.update(task_serializer="json", accept_content=["json"], result_serializer="json")


@celery.task(name="provider.validate_batch")
def validate_batch_task(batch_id: str, items: list):
    """Celery background task that validates a batch of providers.

    Receives serialized provider dicts, reconstructs ProviderInput models,
    and runs the validation service. Updates the batch job status in Redis/DB.
    """
    try:
        from .models import ProviderInput, BatchValidationResponse
        from .services import ValidationService
        from datetime import datetime
        import time

        logger.info(f"Celery worker: starting batch {batch_id} with {len(items)} providers")

        # Reconstruct ProviderInput models from serialized dicts
        providers = []
        for item in items:
            try:
                providers.append(ProviderInput(**item))
            except Exception as e:
                logger.warning(f"Skipping invalid provider dict: {e}")

        # Mark batch as PROCESSING
        batch_response = BatchValidationResponse(
            batch_id=batch_id,
            status="PROCESSING",
            total_providers=len(providers),
            started_at=datetime.utcnow()
        )
        ValidationService._store_batch(batch_id, batch_response)

        # Run validation (synchronous in worker)
        start_time = time.time()
        results = []
        failed = 0

        for provider in providers:
            try:
                result = ValidationService.validate_provider(provider)
                results.append(result)
            except Exception as e:
                logger.error(f"Error validating {provider.provider_name}: {e}")
                failed += 1

        # Update batch to COMPLETED
        batch_response.results = results
        batch_response.completed = len(providers) - failed
        batch_response.failed = failed
        batch_response.status = "COMPLETED"
        batch_response.completed_at = datetime.utcnow()
        batch_response.processing_time_ms = (time.time() - start_time) * 1000

        ValidationService._store_batch(batch_id, batch_response)
        logger.info(f"Celery worker: completed batch {batch_id}")

        return {"batch_id": batch_id, "completed": batch_response.completed, "failed": failed}

    except Exception as exc:
        logger.error(f"Celery worker error for batch {batch_id}: {exc}")
        return {"error": str(exc)}
