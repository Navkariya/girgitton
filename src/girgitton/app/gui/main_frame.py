"""Main frame — guruh ↔ papka jadvali, progress, log, boshqaruv tugmalari.

`v3.1`: Guruhlar `GET /groups?user_id=<>` orqali API'dan keladi va har 30s
da auto-refresh qilinadi (ChatAction listener va `/here` orqali yangilangan
ro'yxatni darhol ko'rsatadi).
"""

from __future__ import annotations

import asyncio
import logging
import tkinter.filedialog as fd
from pathlib import Path
from typing import TYPE_CHECKING, Any

import customtkinter as ctk

from girgitton.app import api_client, config_store, progress_store
from girgitton.app.api_client import APIClient
from girgitton.app.upload.engine import UploadEngine
from girgitton.core.config import SecretStr, Settings

if TYPE_CHECKING:
    from girgitton.app.gui.window import App


logger = logging.getLogger(__name__)

_GROUP_REFRESH_INTERVAL_SECONDS = 30.0


class MainFrame(ctk.CTkFrame):
    def __init__(self, parent: ctk.CTkFrame, app: App) -> None:
        super().__init__(parent, fg_color="transparent")
        self._app = app
        self._engine: UploadEngine | None = None
        self._api_client: APIClient | None = None
        self._running = False

        self._group_vars: dict[int, ctk.StringVar] = {}
        self._group_dones: dict[int, int] = {}
        self._group_totals: dict[int, int] = {}
        self._refresh_task: asyncio.Future[Any] | None = None

        self._idle_client: APIClient | None = None

        self._build_ui()
        self._load_initial_groups()
        self._schedule_group_refresh()
        self._start_idle_polling()
        self._update_resume_btn_state()
        self._schedule_resume_btn_refresh()

    # ─── UI building ──────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            header,
            text="🐈 Girgitton v3.1",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left")
        ctk.CTkButton(
            header,
            text="🔄 Yangilash",
            width=110,
            command=self._on_manual_refresh,
        ).pack(side="right", padx=4)
        ctk.CTkButton(
            header,
            text="Chiqish",
            width=70,
            fg_color="#7f8c8d",
            hover_color="#95a5a6",
            command=self._on_logout,
        ).pack(side="right", padx=4)

        self._groups_frame = ctk.CTkScrollableFrame(
            self, height=140, label_text="🎯 Sizning guruhlaringiz"
        )
        self._groups_frame.pack(fill="x", pady=4, padx=5)

        self._empty_label: ctk.CTkLabel | None = None

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(pady=8)
        self._start_btn = ctk.CTkButton(
            btns,
            text="▶️  Boshlash",
            width=140,
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda: self._on_start(force_resume=False),
        )
        self._start_btn.pack(side="left", padx=6)

        self._resume_btn = ctk.CTkButton(
            btns,
            text="⏯  Davom ettirish",
            width=160,
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#27ae60",
            hover_color="#229954",
            state="disabled",
            command=lambda: self._on_start(force_resume=True),
        )
        self._resume_btn.pack(side="left", padx=6)

        self._stop_btn = ctk.CTkButton(
            btns,
            text="⏹  To'xtatish",
            width=130,
            height=42,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            state="disabled",
            command=self._on_stop,
        )
        self._stop_btn.pack(side="left", padx=6)

        prog = ctk.CTkFrame(self)
        prog.pack(fill="x", pady=8, padx=5)
        self._progress_bar = ctk.CTkProgressBar(prog, height=18)
        self._progress_bar.set(0)
        self._progress_bar.pack(fill="x", padx=15, pady=(15, 5))
        self._prog_label = ctk.CTkLabel(prog, text="Jami: 0/0  (0%)")
        self._prog_label.pack(pady=(2, 10))

        self._log_box = ctk.CTkTextbox(self, height=140, state="disabled", wrap="word")
        self._log_box.pack(fill="both", expand=True, pady=(5, 5), padx=5)

    def _rebuild_groups_ui(self, groups: list[dict[str, Any]]) -> None:
        # Eski papka qiymatlarini saqlab qolamiz
        previous: dict[int, str] = {gid: var.get() for gid, var in self._group_vars.items()}

        for child in self._groups_frame.winfo_children():
            child.destroy()
        self._group_vars.clear()
        self._empty_label = None

        if not groups:
            self._empty_label = ctk.CTkLabel(
                self._groups_frame,
                text=(
                    "Faol guruh yo'q.\n"
                    "Botni guruhga qo'shing va guruhda `/here` yuboring."
                ),
                justify="center",
            )
            self._empty_label.pack(pady=12)
            return

        for g in groups:
            try:
                gid = int(g.get("id"))
            except (TypeError, ValueError):
                continue
            title = g.get("title") or f"Guruh {gid}"
            self._add_group_row(self._groups_frame, gid, title)
            if previous.get(gid):
                self._group_vars[gid].set(previous[gid])

        # Saqlangan papkalarni qayta tiklash
        cfg = config_store.load() or {}
        last = cfg.get("last_folders", {})
        for gid, var in self._group_vars.items():
            if not var.get():
                value = last.get(str(gid))
                if value:
                    var.set(value)

    def _add_group_row(self, parent: ctk.CTkFrame, gid: int, title: str) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)

        ctk.CTkLabel(row, text=f"🎯 {title}", width=180, anchor="w").pack(side="left", padx=5)

        var = ctk.StringVar(value="")
        self._group_vars[gid] = var

        entry = ctk.CTkEntry(row, textvariable=var, state="readonly", height=28)
        entry.pack(side="left", expand=True, fill="x", padx=5)

        ctk.CTkButton(row, text="📂", width=30, command=lambda v=var: self._pick_folder(v)).pack(
            side="right"
        )

        try:
            from tkinterdnd2 import DND_FILES  # type: ignore[import-not-found]

            entry.drop_target_register(DND_FILES)
            entry.dnd_bind("<<Drop>>", lambda e, v=var: self._on_drop(e, v))
        except Exception as exc:
            logger.debug("Drag-drop ulanmagani: %s", exc)

    # ─── Initial groups + auto-refresh ────────────────────────────────────

    def _load_initial_groups(self) -> None:
        cfg = config_store.load() or {}
        groups = cfg.get("groups", []) or []
        self._rebuild_groups_ui(list(groups))
        # API ham so'raymiz (yangi qo'shilgan bo'lsa darhol ko'rsatamiz)
        self._refresh_groups_async()

    def _schedule_group_refresh(self) -> None:
        # Tkinter `after` orqali periodik chaqirish
        self.after(int(_GROUP_REFRESH_INTERVAL_SECONDS * 1000), self._tick_refresh)

    def _tick_refresh(self) -> None:
        self._refresh_groups_async()
        self._schedule_group_refresh()

    def _on_manual_refresh(self) -> None:
        self._log("🔄 Guruhlar ro'yxati yangilanmoqda…")
        self._refresh_groups_async()

    def _refresh_groups_async(self) -> None:
        cfg = config_store.load() or {}
        api_url = cfg.get("api_url", "")
        api_secret = cfg.get("api_secret", "")
        user_id = int(cfg.get("user_id", 0) or 0)
        if not api_url or not user_id:
            return

        async def _fetch() -> list[dict[str, Any]]:
            return await api_client.fetch_groups(api_url, api_secret, user_id)

        fut = self._app.run_async(_fetch())

        def _done(f: Any) -> None:
            try:
                groups = f.result()
            except Exception as exc:
                logger.debug("group refresh error: %s", exc)
                return

            # cfg["groups"] ni yangilab qo'yamiz (next startup uchun)
            cfg2 = config_store.load() or {}
            cfg2["groups"] = groups
            config_store.save(cfg2)
            self._app.ui_callback(self._rebuild_groups_ui, groups)

        fut.add_done_callback(_done)

    # ─── Idle polling (resume/stop signals when not uploading) ────────────

    def _start_idle_polling(self) -> None:
        """Idle holatda ham bot signallariga (`/resume`) javob beradi.

        Yuklash boshlanganda bu polling to'xtatiladi.
        """
        cfg = config_store.load() or {}
        api_url = cfg.get("api_url", "")
        api_secret = cfg.get("api_secret", "")
        user_id = int(cfg.get("user_id", 0) or 0)
        if not api_url or not user_id or self._idle_client is not None:
            return

        client = APIClient(api_url=api_url, api_secret=api_secret, user_id=user_id)
        client.set_resume_callback(self._on_resume_signal)
        self._idle_client = client
        self._app.run_async(client.start_polling())

    async def _stop_idle_polling_async(self) -> None:
        client = self._idle_client
        if client is not None:
            await client.stop_polling()
            self._idle_client = None

    def _update_resume_btn_state(self) -> None:
        """Davom ettirish tugmasi: saqlangan progress bo'lsa enable, aks holda disable."""
        if self._running:
            self._resume_btn.configure(state="disabled")
            return
        has = progress_store.has_resumable()
        self._resume_btn.configure(state="normal" if has else "disabled")

    def _schedule_resume_btn_refresh(self) -> None:
        """Har 3 soniyada tugma holatini tekshiradi (yuklash to'xtagan zaxoti yangilanadi)."""
        if self.winfo_exists():
            self._update_resume_btn_state()
            self.after(3000, self._schedule_resume_btn_refresh)

    def _on_resume_signal(self) -> None:
        """Bot `/resume` signali — agar idle bo'lsa, force_resume=True bilan boshlaymiz."""
        if self._running:
            self._app.ui_callback(self._log, "ℹ️ Resume e'tiborsiz — yuklash davom etmoqda.")
            return
        if not progress_store.has_resumable():
            self._app.ui_callback(self._log, "ℹ️ Saqlangan progress yo'q — resume e'tiborsiz.")
            return
        self._app.ui_callback(self._log, "⏯ Resume signali — saqlangan joydan boshlanmoqda…")
        self._app.ui_callback(self._on_start, force_resume=True)

    # ─── Persist ──────────────────────────────────────────────────────────

    def _persist_folders(self) -> None:
        cfg = config_store.load() or {}
        cfg["last_folders"] = {
            str(gid): var.get() for gid, var in self._group_vars.items() if var.get()
        }
        config_store.save(cfg)

    # ─── UI helpers ───────────────────────────────────────────────────────

    def _pick_folder(self, var: ctk.StringVar) -> None:
        path = fd.askdirectory(title="Media papkasini tanlang", parent=self)
        if path:
            var.set(path)
            self._persist_folders()

    def _on_drop(self, event: Any, var: ctk.StringVar) -> None:
        path = event.data
        if path.startswith("{") and path.endswith("}"):
            path = path[1:-1]
        if Path(path).is_dir():
            var.set(path)
            self._persist_folders()
        else:
            self._log(f"⚠️ Faqat papka tashlanadi (bu fayl): {path}")

    def _log(self, msg: str) -> None:
        self._log_box.configure(state="normal")
        self._log_box.insert("end", msg + "\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")

    def _update_progress(self, group_id: int, done: int, total: int, _speed: float) -> None:
        self._group_dones[group_id] = done
        self._group_totals[group_id] = total
        total_done = sum(self._group_dones.values())
        total_all = sum(self._group_totals.values())
        if total_all > 0:
            pct = total_done / total_all
            self._progress_bar.set(pct)
            self._prog_label.configure(text=f"Jami: {total_done}/{total_all}  ({int(pct * 100)}%)")

    # ─── Lifecycle ────────────────────────────────────────────────────────

    def _on_logout(self) -> None:
        if self._running:
            self._log("⚠️ Avval yuklashni to'xtating!")
            return
        config_store.clear()
        # Restart connect flow
        self._app._bootstrap()

    def _on_start(self, *, force_resume: bool | None = None) -> None:
        group_folders: dict[int, str] = {
            gid: var.get().strip() for gid, var in self._group_vars.items() if var.get().strip()
        }
        if not group_folders:
            self._log("⚠️ Hech bir guruh uchun papka tanlanmagan.")
            return

        cfg = config_store.load()
        if not cfg:
            self._log("⚠️ Config topilmadi. Avval ulaning.")
            return

        for gid, folder in list(group_folders.items()):
            if not Path(folder).is_dir():
                self._log(f"⚠️ Papka mavjud emas: {folder}")
                del group_folders[gid]

        if not group_folders:
            return

        # Resume tanlovi:
        #   force_resume=True   → dialogsiz davom etish (Resume tugmasi yoki /resume)
        #   force_resume=False  → "Boshlash" tugmasi: progress bor bo'lsa CONFIRMATION
        #   force_resume=None   → eski avtomatik dialog
        if force_resume is True:
            resume = True
        elif force_resume is False:
            resume = False
            if progress_store.has_resumable():
                from tkinter import messagebox

                summary = progress_store.summarize()
                proceed = messagebox.askokcancel(
                    "Yangidan boshlash?",
                    f"Saqlangan progress mavjud:\n\n{summary}\n\n"
                    "▶️ Boshlash bossangiz, saqlangan progress o'chiriladi va yangidan boshlanadi.\n"
                    "Davom ettirish uchun ⏯ tugmasidan foydalaning.",
                )
                if not proceed:
                    self._log("Boshlash bekor qilindi.")
                    return
        else:
            resume = False
            if progress_store.has_resumable():
                answer = self._ask_resume_dialog()
                if answer is None:
                    self._log("Boshlash bekor qilindi.")
                    return
                resume = answer

        self._running = True
        self._start_btn.configure(state="disabled")
        self._resume_btn.configure(state="disabled")
        self._stop_btn.configure(state="normal")
        if resume:
            self._log("⏯ Davom ettirilmoqda (saqlangan progressdan)…")
        else:
            self._log("▶️ Yuklash boshlandi (yangidan)…")
            progress_store.clear_all()

        fut = self._app.run_async(self._safe_upload(group_folders, cfg, resume=resume))
        fut.add_done_callback(self._on_async_done)

    def _ask_resume_dialog(self) -> bool | None:
        """Saqlangan progress topilsa — foydalanuvchidan tanlov.

        Returns: True (resume), False (yangidan), None (bekor).
        """
        from tkinter import messagebox

        summary = progress_store.summarize()
        msg = (
            f"Saqlangan tugatilmagan ish topildi:\n\n{summary}\n\n"
            "• Ha — saqlangan joydan davom ettirish\n"
            "• Yo'q — yangidan boshlash (progress o'chiriladi)\n"
            "• Bekor — boshlamaslik"
        )
        return messagebox.askyesnocancel("Davom ettirish", msg)

    def _on_async_done(self, fut: Any) -> None:
        try:
            fut.result()
        except Exception as exc:
            logger.exception("Async upload xatoligi")
            self._app.ui_callback(self._log, f"❌ XATOLIK: {exc}")
            self._app.ui_callback(self._on_upload_done)

    async def _safe_upload(
        self, group_folders: dict[int, str], cfg: dict[str, Any], *, resume: bool = False
    ) -> None:
        try:
            await self._run_upload(group_folders, cfg, resume=resume)
        except Exception as exc:
            logger.exception("Upload xatoligi")
            self._app.ui_callback(self._log, f"❌ XATOLIK: {exc}")
            self._app.ui_callback(self._on_upload_done)

    async def _run_upload(
        self, group_folders: dict[int, str], cfg: dict[str, Any], *, resume: bool = False
    ) -> None:
        api_url = cfg.get("api_url", "")
        api_secret = cfg.get("api_secret", "")
        user_id = int(cfg.get("user_id", 0) or 0)

        settings = Settings(
            api_id=int(cfg["api_id"]),
            api_hash=SecretStr(cfg["api_hash"]),
            bot_token=SecretStr(cfg["bot_token"]),
            api_secret=SecretStr(api_secret),
        )

        first_gid = next(iter(group_folders))

        # Idle pollingni to'xtatamiz — running APIClient o'z polling'i bilan ishlaydi
        await self._stop_idle_polling_async()

        self._api_client = APIClient(api_url=api_url, api_secret=api_secret, user_id=user_id)
        self._api_client.set_stop_callback(self._request_stop)
        await self._api_client.start_polling()

        self._engine = UploadEngine(settings)

        async def notify(msg: str) -> None:
            self._app.ui_callback(self._log, msg)

        def on_progress(group_id: int, done: int, total: int, speed: float) -> None:
            if self._api_client is not None:
                self._api_client.update_status(done, total, speed, current_group=group_id)
            self._app.ui_callback(self._update_progress, group_id, done, total, speed)

        self._api_client.update_status(0, 1, 0.0, current_group=first_gid)

        async def on_throttle(speed: float, wait_secs: int) -> None:
            self._app.ui_callback(self._show_throttle_dialog, speed, wait_secs)
            await asyncio.sleep(wait_secs)

        await self._engine.run(group_folders, notify, on_progress, on_throttle, resume=resume)

        await self._api_client.stop_polling()
        self._app.ui_callback(self._on_upload_done)

    def _request_stop(self) -> None:
        if self._engine is not None:
            self._engine.stop()
        self._app.ui_callback(self._log, "🛑 Stop signali qabul qilindi.")

    def _on_stop(self) -> None:
        if self._engine is not None:
            self._engine.stop()
        self._log("🛑 To'xtatilmoqda…")
        self._stop_btn.configure(state="disabled")

    def _on_upload_done(self) -> None:
        self._running = False
        self._start_btn.configure(state="normal")
        self._stop_btn.configure(state="disabled")
        self._update_resume_btn_state()
        # Idle pollingni qaytarib yoqamiz (yangi /resume signalini qabul qilish uchun)
        self._start_idle_polling()

    def _show_throttle_dialog(self, speed: float, wait_secs: int) -> None:
        from girgitton.app.gui.throttle_dialog import ThrottleDialog

        ThrottleDialog(
            self,
            self._app,
            speed=speed,
            wait_seconds=wait_secs,
            on_retry=lambda: self._log("🔄 Qayta urinish…"),
            on_stop=self._on_stop,
        )

    def on_close(self) -> None:
        if self._running and self._engine is not None:
            self._engine.stop()
