"""User-level runtime patches for local development environment."""

try:
    import pydantic  # type: ignore
    from pydantic_settings import BaseSettings as _BaseSettings  # type: ignore

    pydantic.BaseSettings = _BaseSettings  # type: ignore[attr-defined]
except Exception:
    pass

