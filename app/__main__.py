"""
Desktop App kirish nuqtasi.

Main thread: CustomTkinter GUI (tkinter faqat main thread da xavfsiz)
Background thread: asyncio event loop (upload, API polling)
Ko'prü: run_coroutine_threadsafe + root.after(0, cb)
"""

import asyncio
import threading

from app.gui import App


def _start_async_loop(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_forever()


def main() -> None:
    loop = asyncio.new_event_loop()
    t = threading.Thread(target=_start_async_loop, args=(loop,), daemon=True)
    t.start()

    app = App(loop)
    app.mainloop()

    loop.call_soon_threadsafe(loop.stop)
    t.join(timeout=5)


if __name__ == "__main__":
    main()
