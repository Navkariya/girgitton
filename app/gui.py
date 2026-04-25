"""
App — asosiy CustomTkinter oynasi.

Frame switching: LoginFrame ↔ MainFrame
Config mavjud bo'lsa to'g'ri MainFrame dan ochiladi.
"""

import asyncio
import logging
from typing import Optional

import customtkinter as ctk

from app import app_config

logger = logging.getLogger("girgitton")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

_TITLE = "Girgitton v2"
_WIDTH = 560
_HEIGHT = 620


class App(ctk.CTk):
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        super().__init__()
        self.loop = loop
        self._current_frame: Optional[ctk.CTkFrame] = None

        self.title(_TITLE)
        self.geometry(f"{_WIDTH}x{_HEIGHT}")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._container = ctk.CTkFrame(self, fg_color="transparent")
        self._container.pack(fill="both", expand=True)

        cfg = app_config.load()
        if cfg and cfg.get("bot_token") and cfg.get("display_name"):
            self.show_main()
        else:
            self.show_login()

    def show_login(self) -> None:
        from app.login_frame import LoginFrame
        self._switch_frame(LoginFrame(self._container, self))

    def show_main(self) -> None:
        from app.main_frame import MainFrame
        self._switch_frame(MainFrame(self._container, self))

    def _switch_frame(self, frame: ctk.CTkFrame) -> None:
        if self._current_frame is not None:
            self._current_frame.destroy()
        self._current_frame = frame
        frame.pack(fill="both", expand=True, padx=20, pady=20)

    def run_async(self, coro) -> asyncio.Future:
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    def ui_callback(self, fn, *args) -> None:
        self.after(0, fn, *args)

    def _on_close(self) -> None:
        if self._current_frame and hasattr(self._current_frame, "on_close"):
            self._current_frame.on_close()
        self.destroy()
