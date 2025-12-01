"""Centralized configuration with validation.

Uses pydantic-settings to parse environment variables and enforce basic ranges.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class AppConfig(BaseSettings):
    # Trading
    DAILY_INVESTMENT: float = Field(default=10.0, ge=0.01, description="Daily budget in USD")
    ALPACA_SIMULATED: bool = Field(default=True)
    SIMULATED_EQUITY: float = Field(default=100000.0, ge=0.0)

    # LLM/Budget
    HYBRID_LLM_MODEL: str = Field(default="claude-3-5-haiku-20241022")
    RL_CONFIDENCE_THRESHOLD: float = Field(default=0.6, ge=0.0, le=1.0)
    LLM_NEGATIVE_SENTIMENT_THRESHOLD: float = Field(default=-0.2, le=0.0, ge=-1.0)

    # Risk
    RISK_USE_ATR_SCALING: bool = Field(default=True)
    ATR_STOP_MULTIPLIER: float = Field(default=2.0, gt=0.0)

    @field_validator("DAILY_INVESTMENT")
    @classmethod
    def _validate_budget(cls, v: float) -> float:
        if v > 1000.0:
            raise ValueError("DAILY_INVESTMENT too high for safety; cap at $1000")
        return v

    class Config:
        env_file = ".env"
        extra = "ignore"


def load_config() -> AppConfig:
    return AppConfig()  # type: ignore[call-arg]

