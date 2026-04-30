"""
Tests for backend/scripts/run_worker.py graceful-shutdown behaviour.

Strategy:
  1. Import the module with app deps stubbed in sys.modules.
  2. After import, replace mod.run_worker_loop / mod.record_worker_heartbeat
     with mocks that can set mod._stop to drive loop termination.
  3. Call mod.main() directly (no subprocess needed).

The module-level `_stop = threading.Event()` runs during exec_module and
creates the real event inside the module.  We read it back via mod._stop.
"""
from __future__ import annotations

import importlib.util
import os
import signal
import sys
from unittest.mock import MagicMock, patch

_SCRIPT = os.path.join(os.path.dirname(__file__), "../scripts/run_worker.py")


def _import_worker() -> object:
    """Import run_worker with all heavy application deps stubbed."""
    stubs = {
        "app": MagicMock(),
        "app.modules": MagicMock(),
        "app.modules.jobs": MagicMock(),
        "app.modules.jobs.worker": MagicMock(run_worker_loop=MagicMock(return_value=0)),
        "app.platform": MagicMock(),
        "app.platform.runtime_state": MagicMock(record_worker_heartbeat=MagicMock()),
    }
    with patch.dict(sys.modules, stubs):
        spec = importlib.util.spec_from_file_location("_rw_module", _SCRIPT)
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ---------------------------------------------------------------------------
# Test 1: _handle_signal sets _stop
# ---------------------------------------------------------------------------
def test_sigterm_handler_sets_stop() -> None:
    mod = _import_worker()
    assert not mod._stop.is_set(), "stop should not be set on fresh import"
    mod._handle_signal(signal.SIGTERM, None)
    assert mod._stop.is_set(), "_stop must be set after _handle_signal(SIGTERM)"


# ---------------------------------------------------------------------------
# Test 2: main() calls heartbeat + loop once, then exits with code 0
# ---------------------------------------------------------------------------
def test_main_runs_one_batch_then_exits(monkeypatch) -> None:
    mod = _import_worker()
    call_count = 0

    def _side_effect(iterations: int = 200) -> int:
        nonlocal call_count
        call_count += 1
        mod._stop.set()   # after first batch, signal shutdown
        return 1

    mod.run_worker_loop = MagicMock(side_effect=_side_effect)
    mod.record_worker_heartbeat = MagicMock()

    exited: list[int] = []
    monkeypatch.setattr(sys, "exit", lambda code=0: exited.append(code))

    mod.main()

    assert call_count == 1, "worker loop should run exactly once"
    mod.record_worker_heartbeat.assert_called_once()
    assert exited == [0], "main() must sys.exit(0)"


# ---------------------------------------------------------------------------
# Test 3: Exception in batch is swallowed; loop retries until _stop is set
# ---------------------------------------------------------------------------
def test_exception_in_batch_is_caught(monkeypatch) -> None:
    mod = _import_worker()
    call_count = 0

    def _boom(iterations: int = 200) -> int:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("transient db error")
        mod._stop.set()   # clean exit on second call
        return 0

    mod.run_worker_loop = MagicMock(side_effect=_boom)
    mod.record_worker_heartbeat = MagicMock()
    # Patch _stop.wait so the 1-second inter-batch sleep is instant.
    mod._stop.wait = lambda timeout=None: None  # type: ignore[assignment]

    exited: list[int] = []
    monkeypatch.setattr(sys, "exit", lambda code=0: exited.append(code))

    mod.main()

    assert call_count == 2, "loop should retry once after exception"
    assert exited == [0]
