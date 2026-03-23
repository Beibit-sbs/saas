"""
Workflow Completion Callback Handlers

Handlers for processing workflow completion across different entity types.

Architecture:
- Strategy pattern for entity-type based dispatch
- Decoupled from runtime engine
- Idempotent and fail-closed
- Tenant-first validation
"""
