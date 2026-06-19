"""RBAC permissions for the Digital Twin vertical (read-only at shell stage)."""

STATE_READ = "digital_twin.state.read"
SAFETY_READ = "digital_twin.safety.read"
SIMULATE_RUN = "digital_twin.simulate.run"
DECISION_RECORD = "digital_twin.decision.record"

ALL_PERMISSIONS: frozenset[str] = frozenset({STATE_READ, SAFETY_READ, SIMULATE_RUN, DECISION_RECORD})
DIGITAL_TWIN_PERMISSIONS = sorted(ALL_PERMISSIONS)
DIGITAL_TWIN_PERMISSION_COUNT = len(DIGITAL_TWIN_PERMISSIONS)
