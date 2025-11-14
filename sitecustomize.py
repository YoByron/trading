"""
Runtime patches applied automatically when Python starts in this repo.
"""

try:
    import pydantic  # type: ignore
    from pydantic_settings import BaseSettings as _BaseSettings  # type: ignore

    pydantic.BaseSettings = _BaseSettings  # type: ignore[attr-defined]
except Exception:
    # Fallback silently if the compatibility shim cannot run.
    pass

