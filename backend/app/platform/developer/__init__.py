# Lazy-import avoids circular dependency: uow.py → repository → __init__ → service → uow
# Callers should import from app.platform.developer.service directly.
