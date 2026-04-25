"""
LoginFrame — config import oynasi.

Foydalanuvchi:
  1. "Config import" → fayl tanlaydi (bot /setup faylini)
  2. Ismini kiritadi
  3. "Boshlash" → API /connect → MainFrame ga o'tadi
"""

import logging
import tkinter.filedialog as fd
from typing import TYPE_CHECKING

import customtkinter as ctk

from app import app_config

if TYPE_CHECKING:
    from app.gui import App

logger = logging.getLogger("girgitton")


class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, app: "App") -> None:
        super().__init__(parent, fg_color="transparent")
        self._app = app
        self._cfg: dict | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        # Sarlavha
        ctk.CTkLabel(
            self,
            text="🦎 Girgitton v2",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(pady=(30, 5))

        ctk.CTkLabel(
            self,
            text="Desktop Upload App",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        ).pack(pady=(0, 30))

        # Config import
        cfg_frame = ctk.CTkFrame(self)
        cfg_frame.pack(fill="x", pady=8)

        ctk.CTkLabel(cfg_frame, text="Config fayl:", anchor="w").pack(
            fill="x", padx=15, pady=(12, 0)
        )

        row = ctk.CTkFrame(cfg_frame, fg_color="transparent")
        row.pack(fill="x", padx=15, pady=(4, 12))

        self._cfg_path_var = ctk.StringVar(value="Fayl tanlanmagan")
        ctk.CTkLabel(row, textvariable=self._cfg_path_var, anchor="w", text_color="gray").pack(
            side="left", expand=True, fill="x"
        )
        ctk.CTkButton(row, text="📂 Tanlash", width=100, command=self._pick_config).pack(
            side="right"
        )

        # Ism
        name_frame = ctk.CTkFrame(self)
        name_frame.pack(fill="x", pady=8)

        ctk.CTkLabel(name_frame, text="Ismingiz (caption uchun):", anchor="w").pack(
            fill="x", padx=15, pady=(12, 0)
        )
        self._name_entry = ctk.CTkEntry(
            name_frame, placeholder_text="Ism kiriting...", height=38
        )
        self._name_entry.pack(fill="x", padx=15, pady=(4, 12))

        # Status
        self._status_label = ctk.CTkLabel(
            self, text="", text_color="#e74c3c", wraplength=480
        )
        self._status_label.pack(pady=8)

        # Boshlash tugmasi
        self._start_btn = ctk.CTkButton(
            self,
            text="▶️  Boshlash",
            height=44,
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._on_start,
            state="disabled",
        )
        self._start_btn.pack(pady=16, ipadx=20)

        ctk.CTkLabel(
            self,
            text="Avval Telegram botga /setup yuboring va config faylni yuklab oling.",
            text_color="gray",
            font=ctk.CTkFont(size=11),
            wraplength=460,
        ).pack(pady=(20, 0))

    def _pick_config(self) -> None:
        path = fd.askopenfilename(
            title="Girgitton config faylini tanlang",
            filetypes=[("JSON fayl", "*.json"), ("Barcha fayllar", "*.*")],
        )
        if not path:
            return
        try:
            self._cfg = app_config.import_from_file(path)
            short = path.split("/")[-1] if "/" in path else path.split("\\")[-1]
            self._cfg_path_var.set(f"✅ {short}")
            self._status_label.configure(text="", text_color="#e74c3c")
            self._start_btn.configure(state="normal")
        except Exception as exc:
            self._cfg = None
            self._cfg_path_var.set("Fayl tanlanmagan")
            self._status_label.configure(text=f"⚠️ Fayl xatolik: {exc}")
            self._start_btn.configure(state="disabled")

    def _on_start(self) -> None:
        if not self._cfg:
            self._status_label.configure(text="⚠️ Avval config faylni tanlang.")
            return
        name = self._name_entry.get().strip()
        if not name:
            self._status_label.configure(text="⚠️ Ismingizni kiriting.")
            return

        app_config.set_display_name(name)
        self._status_label.configure(text="🔗 Ulanyapti...", text_color="gray")
        self._start_btn.configure(state="disabled")

        api_url = self._cfg.get("api_url", "")
        api_secret = self._cfg.get("api_secret", "")
        setup_token = self._cfg.get("setup_token", "")

        if api_url and setup_token:
            self._app.run_async(
                self._do_connect(api_url, api_secret, setup_token)
            )
        else:
            self._app.show_main()

    async def _do_connect(self, api_url: str, api_secret: str, setup_token: str) -> None:
        from app.api_client import APIClient

        client = APIClient(
            api_url=api_url,
            api_secret=api_secret,
            user_id=0,
            chat_id=int(self._cfg.get("group_id", 0)),
            setup_token=setup_token,
        )
        ok = await client.connect()
        if ok:
            self._app.ui_callback(self._app.show_main)
        else:
            self._app.ui_callback(
                self._status_label.configure,
                text="⚠️ Bot serverga ulanib bo'lmadi. Internet yoki URL tekshiring.",
                text_color="#e74c3c",
            )
            self._app.ui_callback(self._start_btn.configure, state="normal")
