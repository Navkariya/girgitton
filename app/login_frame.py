"""
LoginFrame — Xavfsiz ulanish oynasi (v2.1).

Foydalanuvchi:
  1. "Lokal Avtomatik ulanish" tugmasini bosadi yoki
  2. Pair kodni kiritib ulanadi
  3. Muvaffaqiyatli ulansa, credentials saqlanib MainFrame ga o'tadi
"""

import logging
from typing import TYPE_CHECKING, Any

import customtkinter as ctk

from app import app_config
from app import api_client

if TYPE_CHECKING:
    from app.gui import App

logger = logging.getLogger("girgitton")


class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, app: "App") -> None:
        super().__init__(parent, fg_color="transparent")
        self._app = app
        self._build_ui()
        self._check_deep_link()

    def _check_deep_link(self) -> None:
        url = getattr(self._app, "_deep_link_url", None)
        if not url:
            return
        
        # girgitton://connect?code=ABC123&server=http://localhost:8080
        from urllib.parse import urlparse, parse_qs
        try:
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)
            if "code" in qs:
                self._code_entry.insert(0, qs["code"][0])
            if "server" in qs:
                # server ni _app ga saqlab qo'yamiz yoki button bosilganda ishlatamiz
                self._app._deep_link_server = qs["server"][0]
        except Exception as exc:
            logger.warning("Deep link parse xatosi: %s", exc)

    def _build_ui(self) -> None:
        # Sarlavha
        ctk.CTkLabel(
            self,
            text="🦎 Girgitton v2.1",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).pack(pady=(30, 5))

        ctk.CTkLabel(
            self,
            text="Secure Pairing",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        ).pack(pady=(0, 30))

        # Auto connect qismi
        auto_frame = ctk.CTkFrame(self)
        auto_frame.pack(fill="x", pady=8, padx=15)
        
        ctk.CTkLabel(auto_frame, text="Lokal ulanish (faqat bitta kompyuterda bo'lsa):").pack(pady=(12, 5))
        
        self._auto_btn = ctk.CTkButton(
            auto_frame,
            text="🔄 Avtomatik ulanish",
            command=self._on_auto_pair,
        )
        self._auto_btn.pack(pady=(5, 15), ipadx=10)

        # Pair code qismi
        code_frame = ctk.CTkFrame(self)
        code_frame.pack(fill="x", pady=8, padx=15)

        ctk.CTkLabel(code_frame, text="Yoki Telegram guruhdan olingan 6 xonali kod:").pack(pady=(12, 5))
        
        self._code_entry = ctk.CTkEntry(
            code_frame, 
            placeholder_text="Masalan: ABC123", 
            justify="center",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=40
        )
        self._code_entry.pack(pady=5, padx=20, fill="x")

        self._pair_btn = ctk.CTkButton(
            code_frame,
            text="✅ Kodni tasdiqlash",
            command=self._on_pair_code,
        )
        self._pair_btn.pack(pady=(5, 15), ipadx=10)

        # Status
        self._status_label = ctk.CTkLabel(
            self, text="", text_color="#e74c3c", wraplength=480
        )
        self._status_label.pack(pady=15)

    def _set_status(self, text: str, is_error: bool = True) -> None:
        color = "#e74c3c" if is_error else "gray"
        self._status_label.configure(text=text, text_color=color)

    def _save_and_proceed(self, data: dict[str, Any]) -> None:
        try:
            # Serverdan kelgan ma'lumotlarni saqlaymiz
            creds = data.get("credentials", {})
            cfg = {
                "api_id": creds.get("api_id"),
                "api_hash": creds.get("api_hash"),
                "bot_token": creds.get("bot_token"),
                "api_url": data.get("api_url"),
                "api_secret": data.get("api_secret", ""),
                "groups": data.get("groups", []),
            }
            # Avvalgi display_name ni saqlab qolish
            old_cfg = app_config.load()
            if old_cfg and "display_name" in old_cfg:
                cfg["display_name"] = old_cfg["display_name"]
            
            app_config.save(cfg)
            self._app.ui_callback(self._app.show_main)
        except Exception as exc:
            self._set_status(f"Saqlashda xatolik: {exc}")

    def _on_auto_pair(self) -> None:
        self._set_status("Ulanmoqda...", is_error=False)
        self._auto_btn.configure(state="disabled")
        self._app.run_async(self._do_auto_pair())

    async def _do_auto_pair(self) -> None:
        data = await api_client.auto_pair()
        self._app.ui_callback(self._auto_btn.configure, state="normal")
        if data.get("ok"):
            self._app.ui_callback(self._save_and_proceed, data)
        else:
            err = data.get("error", "Noma'lum xatolik")
            self._app.ui_callback(self._set_status, f"Avtomatik ulanish xatosi: {err}")

    def _on_pair_code(self) -> None:
        code = self._code_entry.get().strip().upper()
        if not code:
            self._set_status("Kodni kiriting!")
            return
            
        self._set_status("Kod tekshirilmoqda...", is_error=False)
        self._pair_btn.configure(state="disabled")
        
        # Odatda remote server domenini bilishimiz kerak
        server_url = getattr(self._app, "_deep_link_server", "http://127.0.0.1:8080")
        
        self._app.run_async(self._do_pair(server_url, code))

    async def _do_pair(self, server_url: str, code: str) -> None:
        data = await api_client.pair(server_url, code)
        self._app.ui_callback(self._pair_btn.configure, state="normal")
        if data.get("ok"):
            self._app.ui_callback(self._save_and_proceed, data)
        else:
            err = data.get("error", "Noma'lum xatolik")
            self._app.ui_callback(self._set_status, f"Xatolik: {err}")
