"""
Alert dispatching system for autonomous trading bot.

Provides multi-channel alerting (Telegram, email, SMS) to ensure
CEO is immediately notified of any system failures.
"""

from .telegram_alerter import TelegramAlerter

__all__ = ["TelegramAlerter"]
