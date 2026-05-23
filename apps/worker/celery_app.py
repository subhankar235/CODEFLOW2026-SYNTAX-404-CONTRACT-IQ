import os

from celery import Celery

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

app = Celery(
    "contract_iq_worker",
    broker=redis_url,
    backend=redis_url,
    include=[
        "tasks.process_contract",
        "tasks.generate_summary",
        "tasks.generate_counter_offer",
        "tasks.generate_report",
        "tasks.embed_contract",
        "tasks.translate_results",
        "tasks.cleanup_expired_reports",
    ],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "cleanup-expired-reports-every-hour": {
            "task": "tasks.cleanup_expired_reports.cleanup_expired_reports",
            "schedule": 3600.0,
        },
    },
)
