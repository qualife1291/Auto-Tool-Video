"""RED regression: transient SQLite database errors must not kill the worker."""

import sqlite3
from pathlib import Path

import pytest

from auto_tool_video import worker


def test_worker_retries_database_error_during_startup_recovery(monkeypatch, tmp_path):
    recovery_calls = []
    sleeps = []

    class FakeStore:
        def __init__(self):
            self.root = Path(tmp_path)

        def interrupt_running(self):
            recovery_calls.append(True)
            if len(recovery_calls) < 3:
                raise sqlite3.DatabaseError("database disk image is malformed")

    def stop_after_recovery(_store):
        raise KeyboardInterrupt()

    monkeypatch.setattr(worker, "Store", FakeStore)
    monkeypatch.setattr(worker, "run_once", stop_after_recovery)
    monkeypatch.setattr(worker, "collect_garbage", lambda _store: None)
    monkeypatch.setattr(worker.time, "sleep", sleeps.append)
    monkeypatch.setattr(worker.fcntl, "flock", lambda *_: None)

    with pytest.raises(KeyboardInterrupt):
        worker.main()

    assert len(recovery_calls) == 3
    assert sleeps == [0.5, 1.0]


def test_worker_retries_non_operational_sqlite_claim_error_with_capped_backoff(
    monkeypatch, tmp_path
):
    claim_calls = []
    sleeps = []

    class FakeStore:
        def __init__(self):
            self.root = Path(tmp_path)

        def interrupt_running(self):
            pass

    def claim_with_transient_failure(_store):
        claim_calls.append(True)
        if len(claim_calls) <= 6:
            raise sqlite3.DatabaseError("database disk image is malformed")
        raise KeyboardInterrupt()

    monkeypatch.setattr(worker, "Store", FakeStore)
    monkeypatch.setattr(worker, "run_once", claim_with_transient_failure)
    monkeypatch.setattr(worker, "collect_garbage", lambda _store: None)
    monkeypatch.setattr(worker.time, "sleep", sleeps.append)
    monkeypatch.setattr(worker.fcntl, "flock", lambda *_: None)

    with pytest.raises(KeyboardInterrupt):
        worker.main()

    assert len(claim_calls) == 7
    assert sleeps == [0.5, 1.0, 2.0, 4.0, 8.0, 8.0]


def test_worker_propagates_shutdown_during_startup_recovery(monkeypatch, tmp_path):
    class FakeStore:
        def __init__(self):
            self.root = Path(tmp_path)

        def interrupt_running(self):
            raise KeyboardInterrupt()

    monkeypatch.setattr(worker, "Store", FakeStore)
    monkeypatch.setattr(worker.fcntl, "flock", lambda *_: None)

    with pytest.raises(KeyboardInterrupt):
        worker.main()
