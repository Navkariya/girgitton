"""Desktop App entry: `python -m girgitton.app`.

Asosiy thread Tkinter mainloop, ikkilamchi thread asyncio loop.
Bridge: `App.run_async()` + `App.ui_callback()`.
"""

from __future__ import annotations

import asyncio
import logging
import threading

from girgitton.core.logging_setup import setup_logging

logger = logging.getLogger(__name__)


def _start_async_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_forever()


def main() -> None:
    from girgitton.core import app_paths

    setup_logging(
        level="INFO",
        json=False,
        log_dir=app_paths.get_logs_dir(),
        file_name="desktop_app.log",
    )

    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=_start_async_loop, args=(loop,), daemon=True)
    thread.start()

    # Lazy import — customtkinter
    from girgitton.app.gui.window import App

    app = App(loop)
    try:
        app.mainloop()
    finally:
        loop.call_soon_threadsafe(loop.stop)
        thread.join(timeout=5)


if __name__ == "__main__":
    main()
