from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "immigration_doc_reviewer",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    # Individual document processing (OCR + extraction) can involve large
    # scans and a cold-start LLM call - give it real headroom.
    task_time_limit=300,
)

# Make sure tasks are registered.
celery_app.autodiscover_tasks(["app.workers"])
