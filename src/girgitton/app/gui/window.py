"""Asosiy App oynasi (Tkinter root + asyncio loop ko'prigi).

`v3.1`: LoginFrame olib tashlandi. App ochilganda:
  - credentials.enc bor → darhol MainFrame
  - yo'q → connect oqimi (ConnectDialog) → cred saqlash → MainFrame
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import customtkinter as ctk

from girgitton import __version__ as _VERSION
from girgitton.app import config_store, connect_flow

logger = logging.getLogger(__name__)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

_TITLE = f"Girgitton v{_VERSION}"
_WIDTH = 600
_HEIGHT = 660

_DEFAULT_SERVER = os.getenv(
    "GIRGITTON_SERVER",
    "https://web-production-1260c.up.railway.app",
)


class App(ctk.CTk):
    """Tkinter root + tashqi asyncio loop bilan bog'lanish."""

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        *,
        server_url: str = _DEFAULT_SERVER,
    ) -> None:
        super().__init__()
        self.loop = loop
        self.server_url = server_url
        self._current_frame: ctk.CTkFrame | None = None
        self._connect_cancelled = False
        self._connect_dialog: Any = None

        self.title(_TITLE)
        self.geometry(f"{_WIDTH}x{_HEIGHT}")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._set_window_icon()

        self._container = ctk.CTkFrame(self, fg_color="transparent")
        self._container.pack(fill="both", expand=True)

        self._init_drag_drop()
        self._bootstrap()

    def _set_window_icon(self) -> None:
        """girgitton_icon.jpg dan oyna iconini o'rnatadi.

        - Windows: .ico fayl (mavjud bo'lsa) iconbitmap orqali
        - Cross-platform fallback: PIL bilan .jpg → PhotoImage → iconphoto
        """
        # Bundle ichida (PyInstaller `_MEIPASS`), repo strukturasi yoki cwd
        import sys
        from pathlib import Path

        meipass = Path(getattr(sys, "_MEIPASS", "")) if getattr(sys, "frozen", False) else None

        candidates: list[Path] = []
        if meipass:
            candidates.append(meipass / "scripts" / "assets" / "girgitton_icon.jpg")
        candidates += [
            Path(__file__).resolve().parents[3] / "scripts" / "assets" / "girgitton_icon.jpg",
            Path(__file__).resolve().parents[3] / "girgitton_icon.jpg",
            Path("scripts/assets/girgitton_icon.jpg"),
            Path("girgitton_icon.jpg"),
        ]
        ico_candidates: list[Path] = []
        if meipass:
            ico_candidates.append(meipass / "scripts" / "assets" / "icon.ico")
        ico_candidates.append(
            Path(__file__).resolve().parents[3] / "scripts" / "assets" / "icon.ico"
        )

        # Windows .ico (eng yaxshi taskbar uchun)
        for ico in ico_candidates:
            if ico.exists():
                try:
                    self.iconbitmap(str(ico))
                except Exception as exc:
                    logger.debug("iconbitmap xatoligi: %s", exc)
                else:
                    break

        # PNG/JPG → PhotoImage (cross-platform fallback va Linux)
        for jpg in candidates:
            if jpg.exists():
                try:
                    from PIL import Image, ImageTk  # type: ignore[import-not-found]

                    img = Image.open(jpg)
                    img.thumbnail((128, 128))
                    self._icon_image = ImageTk.PhotoImage(img)
                    self.iconphoto(True, self._icon_image)  # type: ignore[arg-type]
                    return
                except Exception as exc:
                    logger.debug("PhotoImage iconi xatoligi: %s", exc)
                    return

    def _init_drag_drop(self) -> None:
        try:
            from tkinterdnd2 import TkinterDnD  # type: ignore[import-not-found]

            self.TkdndVersion = TkinterDnD._require(self)
        except Exception as exc:
            logger.debug("Drag-drop yuklanmadi: %s", exc)

    # ─── Bootstrap ───────────────────────────────────────────────────────

    def _bootstrap(self) -> None:
        cfg = config_store.load()
        if cfg and cfg.get("bot_token") and cfg.get("user_id"):
            saved_url = cfg.get("api_url")
            if saved_url:
                self.server_url = saved_url
            self.show_main()
        else:
            # Cred yo'q — default Railway URL bilan to'g'ridan-to'g'ri connect oqimiga
            saved_url = (cfg or {}).get("api_url")
            if saved_url:
                self.server_url = saved_url
            self._start_connect_flow()

    def _ask_server_url(self, *, default_url: str = "") -> None:
        """Server URL kiritish dialogini ko'rsatadi (Railway URL kiritish uchun)."""
        from girgitton.app.gui.server_dialog import ServerURLDialog

        ServerURLDialog(
            self,
            self,
            on_submit=self._on_server_url_chosen,
            on_cancel=self.destroy,
            default_url=default_url,
        )

    def _on_server_url_chosen(self, url: str) -> None:
        self.server_url = url
        self._start_connect_flow()

    def _start_connect_flow(self) -> None:
        from girgitton.app.gui.connect_dialog import ConnectDialog

        self._connect_cancelled = False
        self._connect_dialog = ConnectDialog(self, self, on_cancel=self._cancel_connect)

        fut = self.run_async(self._do_connect())
        fut.add_done_callback(self._on_connect_done)

    async def _do_connect(self) -> dict[str, Any]:
        return await connect_flow.run_connect_flow(
            self.server_url,
            on_url_ready=lambda url: self.ui_callback(self._set_dialog_url, url),
            on_status=lambda msg: self.ui_callback(self._set_dialog_status, msg),
            is_cancelled=lambda: self._connect_cancelled,
        )

    def _set_dialog_url(self, url: str) -> None:
        if self._connect_dialog is not None:
            self._connect_dialog.set_url(url)

    def _set_dialog_status(self, msg: str) -> None:
        if self._connect_dialog is not None:
            self._connect_dialog.set_status(msg, color="#27ae60")

    def _cancel_connect(self) -> None:
        self._connect_cancelled = True

    def _on_connect_done(self, fut: Any) -> None:
        try:
            result: dict[str, Any] = fut.result()
        except Exception as exc:
            logger.exception("connect xatoligi")
            result = {"error": str(exc)}

        self.ui_callback(self._handle_connect_result, result)

    def _handle_connect_result(self, result: dict[str, Any]) -> None:
        if self._connect_dialog is not None:
            self._connect_dialog.close()
            self._connect_dialog = None

        if not result.get("ok"):
            err = result.get("error", "Noma'lum xatolik")
            logger.warning("Connect xato: %s", err)
            self._show_error_and_retry(err)
            return

        creds = result.get("credentials", {})
        cfg = {
            "user_id": int(result["user_id"]),
            "api_id": creds.get("api_id"),
            "api_hash": creds.get("api_hash"),
            "bot_token": creds.get("bot_token"),
            "api_secret": result.get("api_secret", ""),
            "api_url": result.get("api_url", self.server_url),
            "groups": result.get("groups", []),
        }
        try:
            config_store.save(cfg)
        except Exception as exc:
            logger.exception("Config saqlashda xato")
            self._show_error_and_retry(f"Saqlashda xato: {exc}")
            return

        self.show_main()

    def _show_error_and_retry(self, error: str) -> None:
        from tkinter import messagebox

        msg = (
            f"{error}\n\n"
            f"Hozirgi server: {self.server_url}\n\n"
            "Ha — boshqa server URL kiritish\n"
            "Yo'q — chiqish"
        )
        if messagebox.askyesno("Ulanish xato", msg):
            self._ask_server_url(default_url=self.server_url)
        else:
            self.destroy()

    # ─── Frame switching ─────────────────────────────────────────────────

    def show_main(self) -> None:
        from girgitton.app.gui.main_frame import MainFrame

        self._switch_frame(MainFrame(self._container, self))

    def _switch_frame(self, frame: ctk.CTkFrame) -> None:
        if self._current_frame is not None:
            self._current_frame.destroy()
        self._current_frame = frame
        frame.pack(fill="both", expand=True, padx=20, pady=20)

    # ─── Async bridge ────────────────────────────────────────────────────

    def run_async(self, coro: object) -> Any:
        return asyncio.run_coroutine_threadsafe(coro, self.loop)  # type: ignore[arg-type]

    def ui_callback(self, fn: object, *args: object, **kwargs: object) -> None:
        self.after(0, lambda: fn(*args, **kwargs))  # type: ignore[operator]

    # ─── Lifecycle ───────────────────────────────────────────────────────

    def _on_close(self) -> None:
        if self._current_frame is not None and hasattr(self._current_frame, "on_close"):
            try:
                self._current_frame.on_close()  # type: ignore[attr-defined]
            except Exception:
                logger.exception("on_close xatoligi")
        if self._connect_dialog is not None:
            self._connect_cancelled = True
            self._connect_dialog.close()
        self.destroy()
