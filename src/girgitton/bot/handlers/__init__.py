"""Telegram bot komanda handlerlari."""

from girgitton.bot.handlers.access import register_access
from girgitton.bot.handlers.enrollment import register_enrollment
from girgitton.bot.handlers.help import register_help
from girgitton.bot.handlers.status import register_status

__all__ = ["register_access", "register_enrollment", "register_help", "register_status"]
