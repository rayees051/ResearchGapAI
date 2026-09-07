from celery import Celery
from app.core.config import settings
import os

# Initialize Celery app
celery_app = Celery(
    "research_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Apply configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Allow running tasks synchronously during development if CELERY_ALWAYS_EAGER=true
    task_always_eager=os.getenv("CELERY_ALWAYS_EAGER", "false").lower() == "true"
)
celery_app.conf.imports = (
    "app.tasks.research_tasks",
)

celery_app.autodiscover_tasks(["app.tasks"])
