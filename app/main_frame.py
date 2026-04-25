"""
MainFrame — asosiy ish oynasi.

Tarkibi:
  - Papka tanlash
  - Progress bar + stats (qism, tezlik, qolgan vaqt)
  - Boshlash / To'xtatish tugmalari
  - Log paneli
  - Bot ulanish holati
"""

import asyncio
import logging
import tkinter.filedialog as fd
from typing import TYPE_CHECKING, Optional

import customtkinter as ctk

from app import app_config

if TYPE_CHECKING:
    from app.gui import App

logger = logging.getLogger("girgitton")


class MainFrame(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, app: "App") -> None:
        super().__init__(parent, fg_color="transparent")
        self._app = app
        self._engine: Optional[object] = None
        self._api_client: Optional[object] = None
        self._running = False
        self._total_batches = 0
        self._done_batches = 0
        self._build_ui()
        self._load_last_folder()

    def _build_ui(self) -> None:
        # Sarlavha
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            header,
            text="🦎 Girgitton v2",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left")

        self._status_dot = ctk.CTkLabel(
            header, text="⬤ Bot ulangan", text_color="#2ecc71", font=ctk.CTkFont(size=11)
        )
        self._status_dot.pack(side="right", padx=4)

        # Papka tanlash
        folder_frame = ctk.CTkFrame(self)
        folder_frame.pack(fill="x", pady=4)

        ctk.CTkLabel(folder_frame, text="📁 Papka:", anchor="w", width=80).pack(
            side="left", padx=(12, 4), pady=10
        )
        self._folder_var = ctk.StringVar(value="")
        self._folder_entry = ctk.CTkEntry(
            folder_frame, textvariable=self._folder_var, state="readonly", height=34
        )
        self._folder_entry.pack(side="left", expand=True, fill="x", padx=4)
        ctk.CTkButton(
            folder_frame, text="📂", width=40, command=self._pick_folder
        ).pack(side="right", padx=(4, 12))

        # Guruh
        group_frame = ctk.CTkFrame(self)
        group_frame.pack(fill="x", pady=4)
        group_id = app_config.get("group_id", "—")
        ctk.CTkLabel(
            group_frame,
            text=f"🎯 Guruh:  {group_id}",
            anchor="w",
            text_color="gray",
        ).pack(padx=15, pady=8)

        # Progress panel
        prog_frame = ctk.CTkFrame(self)
        prog_frame.pack(fill="x", pady=8)

        self._stats_label = ctk.CTkLabel(
            prog_frame,
            text="— ta fayl  •  — qism",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self._stats_label.pack(pady=(12, 4))

        self._progress_bar = ctk.CTkProgressBar(prog_frame, height=18)
        self._progress_bar.set(0)
        self._progress_bar.pack(fill="x", padx=15, pady=4)

        self._prog_label = ctk.CTkLabel(
            prog_frame, text="0/0  (0%)", font=ctk.CTkFont(size=12)
        )
        self._prog_label.pack(pady=(2, 4))

        self._speed_label = ctk.CTkLabel(
            prog_frame,
            text="⚡ — MB/s  •  ⏱ —",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        )
        self._speed_label.pack(pady=(0, 12))

        # Tugmalar
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=8)

        self._start_btn = ctk.CTkButton(
            btn_frame,
            text="▶️  Boshlash",
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._on_start,
        )
        self._start_btn.pack(side="left", padx=8)

        self._stop_btn = ctk.CTkButton(
            btn_frame,
            text="⏹  To'xtatish",
            width=140,
            height=40,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            command=self._on_stop,
            state="disabled",
        )
        self._stop_btn.pack(side="left", padx=8)

        # Log panel
        ctk.CTkLabel(self, text="Log:", anchor="w").pack(fill="x", padx=4)
        self._log_box = ctk.CTkTextbox(self, height=130, state="disabled", wrap="word")
        self._log_box.pack(fill="x", pady=(2, 4))

    def _load_last_folder(self) -> None:
        last = app_config.get("last_folder", "")
        if last:
            self._folder_var.set(last)

    def _pick_folder(self) -> None:
        path = fd.askdirectory(title="Media papkasini tanlang")
        if path:
            self._folder_var.set(path)
            app_config.set_last_folder(path)

    def _log(self, msg: str) -> None:
        self._log_box.configure(state="normal")
        self._log_box.insert("end", msg + "\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _update_progress(self, done: int, total: int, speed: float) -> None:
        if total > 0:
            pct = done / total
            self._progress_bar.set(pct)
            self._prog_label.configure(text=f"{done}/{total}  ({int(pct * 100)}%)")

        speed_txt = f"{speed:.2f} MB/s" if speed > 0 else "—"
        self._speed_label.configure(text=f"⚡ {speed_txt}")
        self._done_batches = done
        self._total_batches = total

    def _on_start(self) -> None:
        folder = self._folder_var.get().strip()
        if not folder:
            self._log("⚠️ Papka tanlanmagan.")
            return

        cfg = app_config.load()
        if not cfg:
            self._log("⚠️ Config topilmadi. /setup qayta bajaring.")
            return

        self._running = True
        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._log(f"▶️ Yuklash boshlandi: {folder}")

        self._app.run_async(self._run_upload(folder, cfg))

    async def _run_upload(self, folder: str, cfg: dict) -> None:
        from app.api_client import APIClient
        from app.engine import UploadEngine

        api_url = cfg.get("api_url", "")
        api_secret = cfg.get("api_secret", "")
        setup_token = cfg.get("setup_token", "")
        user_id = int(cfg.get("owner_id", 0))
        chat_id = int(cfg.get("group_id", 0))

        self._api_client = APIClient(
            api_url=api_url,
            api_secret=api_secret,
            user_id=user_id,
            chat_id=chat_id,
            setup_token=setup_token,
        )
        self._api_client.set_stop_callback(self._request_stop)
        await self._api_client.start_polling()

        self._engine = UploadEngine(self._app.loop)

        async def notify(msg: str) -> None:
            self._app.ui_callback(self._log, msg)

        def on_progress(done: int, total: int, speed: float) -> None:
            self._api_client.update_status(done, total, speed)
            self._app.ui_callback(self._update_progress, done, total, speed)

        async def on_throttle(speed: float, wait_secs: int) -> None:
            self._app.ui_callback(self._show_throttle_dialog, speed, wait_secs)
            await asyncio.sleep(wait_secs)

        await self._engine.run(folder, notify, on_progress, on_throttle)

        await self._api_client.stop_polling()
        self._app.ui_callback(self._on_upload_done)

    def _request_stop(self) -> None:
        if self._engine:
            self._engine.stop()
        self._app.ui_callback(self._log, "🛑 Stop signali qabul qilindi.")

    def _on_stop(self) -> None:
        if self._engine:
            self._engine.stop()
        self._log("🛑 To'xtatilmoqda...")
        self._stop_btn.configure(state="disabled")

    def _on_upload_done(self) -> None:
        self._running = False
        self._start_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")

    def _show_throttle_dialog(self, speed: float, wait_secs: int) -> None:
        from app.throttle_dialog import ThrottleDialog

        ThrottleDialog(
            self,
            self._app,
            speed=speed,
            wait_seconds=wait_secs,
            on_retry=lambda: self._log("🔄 Qayta urinish..."),
            on_stop=self._on_stop,
        )

    def on_close(self) -> None:
        if self._running and self._engine:
            self._engine.stop()
