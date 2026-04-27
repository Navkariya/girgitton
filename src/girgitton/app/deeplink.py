"""girgitton:// protokol qo'llab-quvvatlash."""

from __future__ import annotations

import logging
import sys
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger(__name__)

_PROTOCOL = "girgitton"


def parse_deep_link(url: str) -> dict[str, str]:
    """`girgitton://connect?code=ABC123&server=...` ni dict ga ajratadi."""
    if not url.startswith(f"{_PROTOCOL}://"):
        return {}
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    out: dict[str, str] = {}
    for key, values in qs.items():
        if values:
            out[key] = values[0]
    return out


def register_protocol_windows() -> None:
    """Windows reyestrida girgitton:// protokolini ro'yxatdan o'tkazadi."""
    if sys.platform != "win32":
        return

    try:
        import winreg  # type: ignore[import-not-found]

        if getattr(sys, "frozen", False):
            cmd_value = f'"{sys.executable}" "%1"'
        else:
            cmd_value = f'"{sys.executable}" -m girgitton.app "%1"'

        key_path = r"Software\Classes\girgitton"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, "URL:Girgitton Protocol")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
            with winreg.CreateKey(key, r"shell\open\command") as cmd_key:
                winreg.SetValue(cmd_key, "", winreg.REG_SZ, cmd_value)
        logger.info("girgitton:// protokol Windows reyestriga yozildi")
    except Exception as exc:
        logger.debug("Windows reyestriga yozib bo'lmadi: %s", exc)
