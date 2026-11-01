"""Regression: transient SQLite failures during Store construction must not kill the worker."""

import sqlite3

import pytest

from auto_tool_video import worker


@pytest.mark.parametrize(
    ("failures", "expected_sleeps"),
    [
        (2, [0.5, 1.0]),
        (6, [0.5, 1.0, 2.0, 4.0, 8.0, 8.0]),
    ],
)
def test_worker_retries_store_initialization_database_errors(
    monkeypatch, tmp_path, failures, expected_sleeps
):
    attempts = []
    sleeps = []

    class FakeStore:
        root = tmp_path

        def interrupt_running(self):
            pass

    def make_store():
        attempts.append(True)
        if len(attempts) <= failures:
            raise sqlite3.DatabaseError("database is locked during schema initialization")
        return FakeStore()

    def stop_after_recovery(_store):
        raise KeyboardInterrupt()

    monkeypatch.setattr(worker, "Store", make_store)
    monkeypatch.setattr(worker, "run_once", stop_after_recovery)
    monkeypatch.setattr(worker, "collect_garbage", lambda _store: None)
    monkeypatch.setattr(worker.time, "sleep", sleeps.append)
    monkeypatch.setattr(worker.fcntl, "flock", lambda *_: None)

    with pytest.raises(KeyboardInterrupt):
        worker.main()

    assert len(attempts) == failures + 1
    assert sleeps == expected_sleeps


def test_worker_does_not_retry_shutdown_during_store_initialization(monkeypatch):
    calls = []

    def shutdown():
        calls.append(True)
        raise KeyboardInterrupt()

    monkeypatch.setattr(worker, "Store", shutdown)
    with pytest.raises(KeyboardInterrupt):
        worker.main()
    assert len(calls) == 1
