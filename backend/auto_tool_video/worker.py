"""One process owns the queue; an individual malformed job never kills it."""

import fcntl
import logging
import sqlite3
import time

from .generation import run_generation
from .render import render_job
from .store import Store

logger = logging.getLogger(__name__)


def run_once(store: Store) -> bool:
    """Claim and process at most one job; False means the queue was empty.

    Claim failures are surfaced for the loop to retry with backoff. Once claimed,
    unexpected exceptions are isolated to the current job. Do not suppress
    KeyboardInterrupt or SystemExit, which derive from BaseException.
    """
    job = store.claim()
    if job is None:
        return False
    try:
        if job["options"]["kind"] in {"plan", "image"}:
            run_generation(store, job)
        else:
            render_job(store, job)
    except Exception:
        logger.exception("Job %s failed unexpectedly", job["id"])
        try:
            # Render may already have recorded a terminal state. Never overwrite
            # its error report or turn a concurrent cancellation into failure.
            current = store.get("jobs", job["id"])
            if current["state"] == "running":
                store.update_job(
                    job["id"],
                    state="failed",
                    error="Tác vụ thất bại do lỗi xử lý nội bộ. Xem log worker.",
                    error_code="WORKER_ERROR",
                )
        except Exception:
            # A broken/locked DB must not hide the original processing exception
            # or stop subsequent claims. Startup recovery handles stale running jobs.
            logger.exception("Could not persist failure for job %s", job["id"])
    return True


def main() -> None:
    store = Store()
    with (store.root / "worker.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("Worker khác đang chạy cho data directory này.") from None
        store.interrupt_running()
        backoff = 0.5
        while True:
            try:
                processed = run_once(store)
            except sqlite3.OperationalError:
                logger.exception("Queue claim failed; retrying after %.1fs", backoff)
                time.sleep(backoff)
                backoff = min(backoff * 2, 8.0)
                continue
            backoff = 0.5
            if not processed:
                time.sleep(0.5)


if __name__ == "__main__":
    main()
