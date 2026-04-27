"""
MainFrame — asosiy ish oynasi (v2.1 Multi-group).

Tarkibi:
  - Guruhlar ro'yxati va har bir guruh uchun papka tanlash
  - Boshlash / To'xtatish tugmalari
  - Progress bar + stats
  - Log paneli
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
        
        self._group_vars: dict[int, ctk.StringVar] = {}
        self._group_totals: dict[int, int] = {}
        self._group_dones: dict[int, int] = {}

        self._build_ui()
        self._load_last_folders()

    def _build_ui(self) -> None:
        # Sarlavha
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            header,
            text="🦎 Girgitton v2.1",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            header, text="Chiqish", width=60, fg_color="#7f8c8d", hover_color="#95a5a6",
            command=self._on_logout
        ).pack(side="right", padx=4)

        # Guruhlar uchun scrollable frame
        groups_frame = ctk.CTkScrollableFrame(self, height=120)
        groups_frame.pack(fill="x", pady=4, padx=5)

        cfg = app_config.load() or {}
        groups = cfg.get("groups", [])
        
        if not groups:
            ctk.CTkLabel(groups_frame, text="Faol guruhlar yo'q. Avval ulaning.").pack(pady=10)
        
        for g in groups:
            gid = g.get("id")
            title = g.get("title", f"Guruh {gid}")
            
            row = ctk.CTkFrame(groups_frame, fg_color="transparent")
            row.pack(fill="x", pady=4)
            
            ctk.CTkLabel(row, text=f"🎯 {title}", width=120, anchor="w").pack(side="left", padx=5)
            
            var = ctk.StringVar(value="")
            self._group_vars[gid] = var
            
            entry = ctk.CTkEntry(row, textvariable=var, state="readonly", height=28)
            entry.pack(side="left", expand=True, fill="x", padx=5)
            ctk.CTkButton(row, text="📂", width=30, command=lambda v=var: self._pick_folder(v)).pack(side="right")

            try:
                from tkinterdnd2 import DND_FILES
                entry.drop_target_register(DND_FILES)
                entry.dnd_bind('<<Drop>>', lambda e, v=var: self._on_drop(e, v))
            except Exception as e:
                logger.warning(f"Drag & Drop qo'shishda xatolik: {e}")

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

        # Progress panel
        prog_frame = ctk.CTkFrame(self)
        prog_frame.pack(fill="x", pady=8, padx=5)

        self._progress_bar = ctk.CTkProgressBar(prog_frame, height=18)
        self._progress_bar.set(0)
        self._progress_bar.pack(fill="x", padx=15, pady=(15, 5))

        self._prog_label = ctk.CTkLabel(
            prog_frame, text="Jami: 0/0  (0%)", font=ctk.CTkFont(size=12)
        )
        self._prog_label.pack(pady=(2, 10))

        # Log panel
        self._log_box = ctk.CTkTextbox(self, height=120, state="disabled", wrap="word")
        self._log_box.pack(fill="both", expand=True, pady=(5, 5), padx=5)

    def _load_last_folders(self) -> None:
        cfg = app_config.load() or {}
        last_folders = cfg.get("last_folders", {})
        for gid, var in self._group_vars.items():
            if str(gid) in last_folders:
                var.set(last_folders[str(gid)])

    def _save_last_folders(self) -> None:
        cfg = app_config.load() or {}
        last_folders = {str(gid): var.get() for gid, var in self._group_vars.items() if var.get()}
        cfg["last_folders"] = last_folders
        app_config.save(cfg)

    def _pick_folder(self, var: ctk.StringVar) -> None:
        path = fd.askdirectory(title="Media papkasini tanlang", parent=self)
        if path:
            var.set(path)
            self._save_last_folders()

    def _on_drop(self, event, var: ctk.StringVar) -> None:
        import os
        path = event.data
        if path.startswith('{') and path.endswith('}'):
            path = path[1:-1]
        
        if os.path.isdir(path):
            var.set(path)
            self._save_last_folders()
        else:
            self._log(f"⚠️ Faqat papka tashlash mumkin. Bu fayl: {path}")

    def _log(self, msg: str) -> None:
        self._log_box.configure(state="normal")
        self._log_box.insert("end", msg + "\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _update_progress(self, group_id: int, done: int, total: int, speed: float) -> None:
        self._group_dones[group_id] = done
        self._group_totals[group_id] = total
        
        total_done = sum(self._group_dones.values())
        total_all = sum(self._group_totals.values())
        
        if total_all > 0:
            pct = total_done / total_all
            self._progress_bar.set(pct)
            self._prog_label.configure(text=f"Jami: {total_done}/{total_all}  ({int(pct * 100)}%)")

    def _on_logout(self) -> None:
        if self._running:
            self._log("Avval yuklashni to'xtating!")
            return
        app_config.clear()
        self._app.ui_callback(self._app.show_login)

    def _on_start(self) -> None:
        group_folders = {gid: var.get().strip() for gid, var in self._group_vars.items() if var.get().strip()}
        
        if not group_folders:
            self._log("⚠️ Hech qaysi guruh uchun papka tanlanmagan.")
            return

        cfg = app_config.load()
        if not cfg:
            self._log("⚠️ Config topilmadi. Avval ulaning.")
            return

        # Papka mavjudligini tekshirish
        from pathlib import Path
        for gid, folder in list(group_folders.items()):
            folder_path = Path(folder)
            if not folder_path.exists() or not folder_path.is_dir():
                self._log(f"⚠️ Papka topilmadi yoki xato: {folder}")
                del group_folders[gid]

        if not group_folders:
            return

        self._running = True
        self._start_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        self._log("▶️ Yuklash boshlandi")

        fut = self._app.run_async(self._safe_upload(group_folders, cfg))
        fut.add_done_callback(self._on_async_done)

    def _on_async_done(self, fut) -> None:
        try:
            fut.result()
        except Exception as exc:
            logger.error("Async upload xatolik: %s", exc, exc_info=True)
            self._app.ui_callback(self._log, f"❌ XATOLIK: {exc}")
            self._app.ui_callback(self._on_upload_done)

    async def _safe_upload(self, group_folders: dict[int, str], cfg: dict) -> None:
        try:
            await self._run_upload(group_folders, cfg)
        except Exception as exc:
            logger.error("Upload xatolik: %s", exc, exc_info=True)
            self._app.ui_callback(self._log, f"❌ XATOLIK: {exc}")
            self._app.ui_callback(self._on_upload_done)

    async def _run_upload(self, group_folders: dict[int, str], cfg: dict) -> None:
        from app.api_client import APIClient
        from app.engine import UploadEngine

        api_url = cfg.get("api_url", "")
        api_secret = cfg.get("api_secret", "")
        user_id = int(cfg.get("owner_id", cfg.get("user_id", 0)))
        
        # Asosiy chat_id sifatida birinchisini olamiz (API client uchun)
        first_group = list(group_folders.keys())[0]

        self._api_client = APIClient(
            api_url=api_url,
            api_secret=api_secret,
            user_id=user_id,
        )
        self._api_client.set_stop_callback(self._request_stop)
        await self._api_client.start_polling()

        self._engine = UploadEngine(self._app.loop)

        async def notify(msg: str) -> None:
            self._app.ui_callback(self._log, msg)

        def on_progress(group_id: int, done: int, total: int, speed: float) -> None:
            self._api_client.update_status(done, total, speed, current_group=group_id)
            self._app.ui_callback(self._update_progress, group_id, done, total, speed)

        # Boshlanishida statusni yangilab qo'yamiz (0%)
        self._api_client.update_status(0, 1, 0.0, current_group=first_group)

        async def on_throttle(speed: float, wait_secs: int) -> None:
            self._app.ui_callback(self._show_throttle_dialog, speed, wait_secs)
            await asyncio.sleep(wait_secs)

        await self._engine.run(group_folders, notify, on_progress, on_throttle)

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
