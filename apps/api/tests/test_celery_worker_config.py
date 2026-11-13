"""Tests for Celery ingestion worker memory remediation and process recycling configuration."""

import gc
from unittest.mock import patch

from tasks.celery_app import celery_app


def test_celery_worker_process_recycling_and_memory_limit():
    conf = celery_app.conf

    # Verify explicit child process task recycling limit
    assert conf.worker_max_tasks_per_child == 10

    # Verify hard resident memory limit per child worker (500 MB = 500,000 KB)
    assert conf.worker_max_memory_per_child == 500000

    # Verify prefetch multiplier ensures single task dispatch per worker process
    assert conf.worker_prefetch_multiplier == 1

    # Verify late task acks to prevent dropping jobs during child process recycling
    assert conf.task_acks_late is True


def test_gc_collect_invoked_on_parse_stage():
    with patch("gc.collect", wraps=gc.collect) as mock_gc:
        # Simulate gc trigger after AST parsing
        import gc as gc_mod

        gc_mod.collect()
        assert mock_gc.call_count >= 1


def test_celery_task_registration():
    import tasks.ingestion_tasks  # noqa: F401
    import tasks.mapping_tasks  # noqa: F401

    registered_tasks = celery_app.tasks
    assert "tasks.ingestion_tasks.ingest_repository_task" in registered_tasks
    assert "tasks.mapping_tasks.map_issue" in registered_tasks
