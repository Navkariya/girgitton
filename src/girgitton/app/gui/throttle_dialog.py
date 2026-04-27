"""Telegram throttle dialog (countdown taymer + retry/stop)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import customtkinter as ctk

if TYPE_CHECKING:
    from collections.abc import Callable

    from girgitton.app.gui.window import App


logger = logging.getLogger(__name__)


class ThrottleDialog(ctk.CTkToplevel):
    def __init__(
        self,
        parent: ctk.CTkFrame,
        app: App,
        *,
        speed: float,
        wait_seconds: int,
        on_retry: Callable[[], None] | None = None,
        on_stop: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self._app = app
        self._speed = speed
        self._remaining = wait_seconds
        self._on_retry = on_retry
        self._on_stop = on_stop
        self._cancelled = False

        self.title("⚠️ Telegram Throttle")
        self.geometry("440x340")
        self.resizable(False, False)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._do_stop)

        self._build_ui()
        self._tick()

    def _build_ui(self) -> None:
        ctk.CTkLabel(
            self,
            text="⚠️  Telegram tezlikni chekladi",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#e67e22",
        ).pack(pady=(24, 8))

        ctk.CTkLabel(
            self,
            text=(
                f"Tezlik: {self._speed:.2f} MB/s  (normal: ~1.0 MB/s)\n"
                "Sessiyani yangilash yordam bermadi.\n\n"
                "Sabab: Telegram akkaunt darajasida throttle.\n"
                "Bu vaqtincha — odatda 30-60 daqiqada ochiladi."
            ),
            font=ctk.CTkFont(size=12),
            justify="center",
        ).pack(pady=8)

        ctk.CTkLabel(
            self,
            text="Progress saqlangan — hech narsa yo'qolmaydi.",
            text_color="gray",
            font=ctk.CTkFont(size=11),
        ).pack()

        self._timer_label = ctk.CTkLabel(
            self,
            text=self._format_time(self._remaining),
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#3498db",
        )
        self._timer_label.pack(pady=16)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=8)

        ctk.CTkButton(
            btn_frame,
            text="Hozir qayta urinish",
            width=170,
            command=self._do_retry,
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame,
            text="To'xtatish",
            width=130,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self._do_stop,
        ).pack(side="left", padx=8)

    @staticmethod
    def _format_time(seconds: int) -> str:
        m, s = divmod(max(0, seconds), 60)
        return f"⏱ Avto-retry: {m:02d}:{s:02d}"

    def _tick(self) -> None:
        if self._cancelled:
            return
        self._remaining -= 1
        self._timer_label.configure(text=self._format_time(self._remaining))
        if self._remaining <= 0:
            self._do_retry()
        else:
            self.after(1000, self._tick)

    def _do_retry(self) -> None:
        self._cancelled = True
        self.destroy()
        if self._on_retry is not None:
            try:
                self._on_retry()
            except Exception:
                logger.exception("on_retry xatoligi")

    def _do_stop(self) -> None:
        self._cancelled = True
        self.destroy()
        if self._on_stop is not None:
            try:
                self._on_stop()
            except Exception:
                logger.exception("on_stop xatoligi")
