import fcntl
import subprocess
import time

from .render import render_job
from .store import DomainError, Store


def main() -> None:
    store = Store()
    with (store.root / "worker.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("Worker khác đang chạy cho data directory này.") from None
        store.interrupt_running()
        while True:
            job = store.claim()
            if job:
                try:
                    render_job(store, job)
                except (RuntimeError, OSError, ValueError, subprocess.SubprocessError, DomainError):
                    print(f"Job {job['id']}: RENDER_FAILED", flush=True)
            else:
                time.sleep(0.5)


if __name__ == "__main__":
    main()
