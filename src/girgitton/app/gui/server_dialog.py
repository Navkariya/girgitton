"""Server URL kiritish dialogi (lokal bot ishlamasa Railway URL so'raydi)."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

import customtkinter as ctk

if TYPE_CHECKING:
    from girgitton.app.gui.window import App


logger = logging.getLogger(__name__)


class ServerURLDialog(ctk.CTkToplevel):
    """Foydalanuvchidan bot server URL'ini kiritishini so'raydi."""

    def __init__(
        self,
        parent: ctk.CTk | ctk.CTkFrame,
        app: App,
        *,
        on_submit: Callable[[str], None],
        on_cancel: Callable[[], None],
        default_url: str = "",
    ) -> None:
        super().__init__(parent)
        self._app = app
        self._on_submit = on_submit
        self._on_cancel = on_cancel

        self.title("Girgitton — Server URL")
        self.geometry("520x320")
        self.resizable(False, False)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._do_cancel)
        self._inherit_icon()

        self._build_ui(default_url)

    def _inherit_icon(self) -> None:
        try:
            icon = getattr(self._app, "_icon_image", None)
            if icon is not None:
                self.iconphoto(False, icon)  # type: ignore[arg-type]
        except Exception:
            pass

    def _build_ui(self, default_url: str) -> None:
        ctk.CTkLabel(
            self,
            text="🌐 Bot server URL'i",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(pady=(20, 8))

        ctk.CTkLabel(
            self,
            text=(
                "Bot Railway yoki boshqa serverda ishlasa, uning URL'ini kiriting.\n"
                "Lokal bot uchun: http://127.0.0.1:8080"
            ),
            justify="center",
            wraplength=460,
            font=ctk.CTkFont(size=12),
        ).pack(pady=8, padx=20)

        self._entry = ctk.CTkEntry(
            self,
            placeholder_text="https://your-app.up.railway.app",
            font=ctk.CTkFont(size=14),
            height=40,
            width=440,
        )
        self._entry.pack(pady=12, padx=20, fill="x")
        if default_url:
            self._entry.insert(0, default_url)
        self._entry.bind("<Return>", lambda _e: self._do_submit())

        self._error_label = ctk.CTkLabel(self, text="", text_color="#e74c3c")
        self._error_label.pack(pady=4)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=10)

        ctk.CTkButton(
            btn_row,
            text="✅ Davom etish",
            width=170,
            height=40,
            command=self._do_submit,
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_row,
            text="Bekor qilish",
            width=130,
            height=40,
            fg_color="#7f8c8d",
            hover_color="#95a5a6",
            command=self._do_cancel,
        ).pack(side="left", padx=8)

    def _do_submit(self) -> None:
        url = self._entry.get().strip().rstrip("/")
        if not url:
            self._error_label.configure(text="URL kiritilmagan!")
            return
        if not url.startswith(("http://", "https://")):
            self._error_label.configure(text="URL http:// yoki https:// bilan boshlansin!")
            return
        self._on_submit(url)
        self.destroy()

    def _do_cancel(self) -> None:
        try:
            self._on_cancel()
        finally:
            try:
                self.destroy()
            except Exception:
                pass
