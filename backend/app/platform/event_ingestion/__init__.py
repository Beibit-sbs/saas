"""Platform event ingestion layer v1.

Provides a centralized record_event() function that writes lightweight
platform events (analytics reads, billing usage) as an append-only data trail.
This is separate from the outbox pattern (domain events → processing pipeline).
"""
