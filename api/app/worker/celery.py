"""Celery worker configuration and tasks."""
from celery import Celery

from app.core.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "bananapics",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
    include=["app.worker.tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Broker settings
    broker_connection_retry_on_startup=True,
    
    # Task settings
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=270,  # 4.5 minutes
    
    # Result settings
    result_expires=3600,  # 1 hour
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
    
    # Beat schedule (if needed)
    beat_schedule={
        "cleanup-expired-generations": {
            "task": "app.worker.tasks.cleanup_expired_generations",
            "schedule": 3600.0,  # Every hour
        },
    },
)
