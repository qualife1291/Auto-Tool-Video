"""Worker RED regression: one broken job must not poison the queue."""

import json
import sqlite3
from pathlib import Path

import pytest

from auto_tool_video import worker
from auto_tool_video.store import Store


class Queue:
    def __init__(self):
        self.jobs = [
            {"id": "bad", "state": "queued", "options": {"kind": "export"}},
            {"id": "good", "state": "queued", "options": {"kind": "export"}},
        ]
        self.updated = {}

    def claim(self):
        for job in self.jobs:
            if job["state"] == "queued":
                job["state"] = "running"
                return job.copy()
        return None

    def get(self, table, identifier):
        assert table == "jobs"
        return next(job.copy() for job in self.jobs if job["id"] == identifier)

    def update_job(self, identifier, **changes):
        job = next(job for job in self.jobs if job["id"] == identifier)
        job.update(changes)
        self.updated[identifier] = changes
        return job.copy()


@pytest.mark.parametrize("error", [KeyError("bad frame"), sqlite3.OperationalError("locked")])
def test_worker_isolates_unhandled_render_error_and_continues(monkeypatch, error):
    queue = Queue()
    rendered = []

    def render(store, job):
        rendered.append(job["id"])
        if job["id"] == "bad":
            raise error
        store.update_job(job["id"], state="succeeded")

    monkeypatch.setattr(worker, "render_job", render)
    assert worker.run_once(queue)
    assert queue.get("jobs", "bad")["state"] == "failed"
    assert queue.get("jobs", "bad")["error_code"] == "WORKER_ERROR"
    assert worker.run_once(queue)
    assert queue.get("jobs", "good")["state"] == "succeeded"
    assert not worker.run_once(queue)
    assert rendered == ["bad", "good"]


def test_worker_does_not_overwrite_terminal_job_state(monkeypatch):
    queue = Queue()

    def render(store, job):
        store.update_job(job["id"], state="failed", error="specific decoder failure")
        raise ValueError("late exception")

    monkeypatch.setattr(worker, "render_job", render)
    assert worker.run_once(queue)
    assert queue.get("jobs", "bad")["error"] == "specific decoder failure"
    assert queue.updated["bad"]["error"] == "specific decoder failure"


@pytest.mark.parametrize("shutdown", [KeyboardInterrupt(), SystemExit("stop")])
def test_explicit_shutdown_propagates(monkeypatch, shutdown):
    queue = Queue()

    def render(_store, _job):
        raise shutdown

    monkeypatch.setattr(worker, "render_job", render)
    with pytest.raises(type(shutdown)):
        worker.run_once(queue)


def test_transient_claim_lock_has_bounded_backoff(monkeypatch, tmp_path):
    calls = []
    sleeps = []

    class FakeStore:
        def __init__(self):
            self.root = Path(tmp_path)

        def interrupt_running(self):
            pass

    def run(_store):
        calls.append(True)
        if len(calls) <= 3:
            raise sqlite3.OperationalError("database is locked")
        return False

    def sleep(seconds):
        sleeps.append(seconds)
        if len(sleeps) >= 4:
            raise KeyboardInterrupt()

    monkeypatch.setattr(worker, "Store", FakeStore)
    monkeypatch.setattr(worker, "run_once", run)
    monkeypatch.setattr(worker.time, "sleep", sleep)
    monkeypatch.setattr(worker.fcntl, "flock", lambda *_: None)
    with pytest.raises(KeyboardInterrupt):
        worker.main()
    assert sleeps == [0.5, 1.0, 2.0, 0.5]



@pytest.mark.parametrize("error", [KeyError("bad shape"), sqlite3.OperationalError("db write")])
def test_real_sqlite_queue_survives_two_sequential_jobs(tmp_path, monkeypatch, error):
    store = Store(tmp_path)
    for identifier in ("broken", "following"):
        job = {
            "id": identifier,
            "project_id": "regression",
            "state": "queued",
            "options": {"kind": "export"},
        }
        with store.connect() as conn:
            conn.execute(
                "INSERT INTO jobs VALUES(?,?,?,?,?,?)",
                (identifier, "regression", identifier, "hash", "queued", json.dumps(job)),
            )

    def render(actual_store, job):
        if job["id"] == "broken":
            raise error
        actual_store.update_job(job["id"], state="succeeded", result_id="tested")

    monkeypatch.setattr(worker, "render_job", render)
    assert worker.run_once(store) is True
    first = store.get("jobs", "broken")
    assert first["state"] == "failed"
    assert first["error_code"] == "WORKER_ERROR"
    assert worker.run_once(store) is True
    second = store.get("jobs", "following")
    assert second["state"] == "succeeded"
    assert second["result_id"] == "tested"
    assert worker.run_once(store) is False
