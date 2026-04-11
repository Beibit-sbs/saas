#!/usr/bin/env python
"""
Worker entrypoint with graceful SIGTERM / SIGINT shutdown.

Replaces the bare 'while true; do python ...; sleep 1; done' bash loop in
docker-compose.yml.  When Docker sends SIGTERM the current job-batch (up to
200 iterations) is allowed to finish, then the process exits cleanly with
code 0.
"""
from __future__ import annotations

import signal
import sys
import threading

_stop = threading.Event()


def _handle_signal(signum: int, _frame: object) -> None:
    print(f"[worker] received signal {signum}, shutting down after current batch…", flush=True)
    _stop.set()


signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)

# Import after signal setup so startup errors are visible before any loop runs.
from app.modules.jobs.worker import run_worker_loop  # noqa: E402
from app.platform.runtime_state import record_worker_heartbeat  # noqa: E402

def main() -> None:
    print("[worker] loop started", flush=True)
    while not _stop.is_set():
        try:
            record_worker_heartbeat()
            run_worker_loop(iterations=200)
        except Exception as exc:  # noqa: BLE001
            print(f"[worker] error in batch: {exc}", flush=True)
        # Wait up to 1 s before next batch; returns immediately when _stop is set.
        _stop.wait(timeout=1.0)
    print("[worker] exited cleanly", flush=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
