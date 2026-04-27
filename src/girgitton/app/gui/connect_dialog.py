"""Connect modal — Telegram'da START bosishni kutish."""

from __future__ import annotations

import logging
import webbrowser
from collections.abc import Callable
from typing import TYPE_CHECKING

import customtkinter as ctk

if TYPE_CHECKING:
    from girgitton.app.gui.window import App


logger = logging.getLogger(__name__)


class ConnectDialog(ctk.CTkToplevel):
    """Foydalanuvchini Telegram'ga yo'naltiruvchi modal."""

    def __init__(
        self,
        parent: ctk.CTk | ctk.CTkFrame,
        app: App,
        *,
        on_cancel: Callable[[], None],
    ) -> None:
        super().__init__(parent)
        self._app = app
        self._on_cancel = on_cancel
        self._url: str | None = None

        self.title("Girgitton — Ulanish")
        self.geometry("480x340")
        self.resizable(False, False)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._do_cancel)
        self._inherit_icon()

        self._build_ui()

    def _inherit_icon(self) -> None:
        """Asosiy oyna iconini ushbu modal uchun ham qo'llash."""
        try:
            icon = getattr(self._app, "_icon_image", None)
            if icon is not None:
                self.iconphoto(False, icon)  # type: ignore[arg-type]
        except Exception:
            pass

    def _build_ui(self) -> None:
        ctk.CTkLabel(
            self,
            text="🐈 Girgitton ga ulanish",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(pady=(20, 10))

        ctk.CTkLabel(
            self,
            text=(
                "Telegram brauzerda ochildi.\n"
                "Botda **START** tugmasini bosing — App avtomatik ulanadi."
            ),
            justify="center",
            font=ctk.CTkFont(size=13),
            wraplength=420,
        ).pack(pady=8)

        self._status_label = ctk.CTkLabel(
            self,
            text="⏳ Telegram javobi kutilmoqda…",
            text_color="#3498db",
            font=ctk.CTkFont(size=12),
        )
        self._status_label.pack(pady=10)

        self._link_label = ctk.CTkLabel(
            self,
            text="(URL hali tayyor emas)",
            text_color="gray",
            wraplength=420,
            cursor="hand2",
        )
        self._link_label.pack(pady=8)
        self._link_label.bind("<Button-1>", lambda _e: self._open_url())

        ctk.CTkButton(
            self,
            text="🔗 Linkni qayta ochish",
            command=self._open_url,
        ).pack(pady=6)

        ctk.CTkButton(
            self,
            text="Bekor qilish",
            fg_color="#7f8c8d",
            hover_color="#95a5a6",
            command=self._do_cancel,
        ).pack(pady=6)

    def set_url(self, url: str) -> None:
        self._url = url
        self._link_label.configure(text=url, text_color="#3498db")

    def set_status(self, msg: str, *, color: str = "#3498db") -> None:
        self._status_label.configure(text=msg, text_color=color)

    def _open_url(self) -> None:
        if self._url:
            try:
                webbrowser.open(self._url)
            except Exception:
                logger.debug("webbrowser.open ishlamadi")

    def _do_cancel(self) -> None:
        try:
            self._on_cancel()
        finally:
            try:
                self.destroy()
            except Exception:
                pass

    def close(self) -> None:
        try:
            self.destroy()
        except Exception:
            pass
