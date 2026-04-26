"""
Desktop App kirish nuqtasi.

Main thread: CustomTkinter GUI (tkinter faqat main thread da xavfsiz)
Background thread: asyncio event loop (upload, API polling)
Ko'prü: run_coroutine_threadsafe + root.after(0, cb)
"""

import asyncio
import logging
import sys
import threading
from pathlib import Path

# Windows konsoli UTF-8 emojilarni ko'rsatishi uchun
for stream in (sys.stdout, sys.stderr):
    if stream and hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _register_windows_protocol() -> None:
    """Windows reyestrida girgitton:// protocolini ro'yxatdan o'tkazadi."""
    if sys.platform != "win32":
        return
        
    try:
        import winreg
        
        # PyInstaller orqali .exe dan ishlaganda exe yo'lini olish
        if getattr(sys, "frozen", False):
            app_path = sys.executable
        else:
            app_path = sys.executable + f' "{sys.argv[0]}"'

        key_path = r"Software\Classes\girgitton"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValue(key, "", winreg.REG_SZ, "URL:Girgitton Protocol")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
            
            with winreg.CreateKey(key, r"shell\open\command") as cmd_key:
                winreg.SetValue(cmd_key, "", winreg.REG_SZ, f'"{app_path}" "%1"')
                
    except Exception as exc:
        logging.getLogger("girgitton").debug("Windows reyestriga yozishda xatolik: %s", exc)


def _setup_app_logging() -> None:
    """Desktop App uchun logging sozlash."""
    log_dir = Path.home() / ".girgitton"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "desktop_app.log"

    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handlers = [
        logging.StreamHandler(sys.stderr),
        logging.FileHandler(str(log_file), encoding="utf-8"),
    ]
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers)
    logging.getLogger("girgitton").info("Desktop App logging boshlandi: %s", log_file)


from app.gui import App


def _start_async_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_forever()


def main() -> None:
    _setup_app_logging()
    _register_windows_protocol()

    deep_link_url = None
    if len(sys.argv) > 1 and sys.argv[1].startswith("girgitton://"):
        deep_link_url = sys.argv[1]
        logging.getLogger("girgitton").info("Deep link orqali ochildi: %s", deep_link_url)

    loop = asyncio.new_event_loop()
    t = threading.Thread(target=_start_async_loop, args=(loop,), daemon=True)
    t.start()

    app = App(loop, deep_link_url=deep_link_url)
    app.mainloop()

    loop.call_soon_threadsafe(loop.stop)
    t.join(timeout=5)


if __name__ == "__main__":
    main()
