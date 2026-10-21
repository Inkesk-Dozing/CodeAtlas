"""Celery application for long-running ingestion and mapping workloads.

Short tasks (single-repo ingestion) still run via FastAPI BackgroundTasks by
default; enable `settings.use_celery` to route them through this worker instead.
"""
from __future__ import annotations

from celery import Celery
from celery.signals import task_failure, task_success

from config import settings

celery_app = Celery(
    "codeatlas",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["tasks.ingestion_tasks", "tasks.mapping_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=1800,
    task_time_limit=3600,
    result_expires=3600 * 6,
    task_routes={
        "tasks.ingestion_tasks.*": {"queue": "ingestion"},
        "tasks.mapping_tasks.*": {"queue": "mapping"},
    },
    task_default_queue="default",
    broker_transport_options={"visibility_timeout": 3600},
)


@task_success.connect
def _on_task_success(sender, **kwargs):
    import logging

    logging.getLogger("celery").info("task %s succeeded", sender.name)


@task_failure.connect
def _on_task_failure(sender, task_id, exception, **kwargs):
    import logging

    logging.getLogger("celery").error(
        "task %s (%s) failed: %s", sender.name, task_id, exception
    )
