"""Digital Twin / Predictive Operations vertical (A-056).

Read-only observation + simulation layer over existing signals and capacity
sources. No data store of its own at shell stage; no autonomous action.

Operating principle:
    Brain sees. Digital twin simulates. Workflow proposes. Human approves. Audit records.
"""

MODULE_NAME = "digital_twin"
API_PREFIX = "/api/admin/digital-twin"
RUNTIME_MODE = "METADATA_OBSERVATION_SIMULATION_HUMAN_REVIEW_ONLY"
EXPECTED_ROUTE_COUNT = 3
