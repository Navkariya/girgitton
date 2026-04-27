# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — Girgitton Desktop App."""

import os
import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent

try:
    import tkinterdnd2  # type: ignore[import-not-found]

    tkdnd_path = os.path.join(os.path.dirname(tkinterdnd2.__file__), "tkdnd")
except ImportError:
    tkdnd_path = None

datas = []
if tkdnd_path:
    datas.append((tkdnd_path, "tkinterdnd2/tkdnd"))

# girgitton_icon.jpg ni bundle ichiga qo'shamiz (window iconphoto uchun)
_icon_jpg = ROOT / "scripts" / "assets" / "girgitton_icon.jpg"
if _icon_jpg.exists():
    datas.append((str(_icon_jpg), "scripts/assets"))

# Loyiha ikonkasi (assets/ ichida)
icon_dir = ROOT / "scripts" / "assets"
icon_dir.mkdir(parents=True, exist_ok=True)
icon_win = icon_dir / "icon.ico"
icon_mac = icon_dir / "icon.icns"

a = Analysis(
    [str(ROOT / "src" / "girgitton" / "app" / "__main__.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "customtkinter",
        "tkinterdnd2",
        "telethon",
        "aiohttp",
        "cryptography",
        "girgitton",
        "girgitton.app",
        "girgitton.app.gui.window",
        "girgitton.app.gui.login_frame",
        "girgitton.app.gui.main_frame",
        "girgitton.app.gui.throttle_dialog",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=["pytest", "redis"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Girgitton",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    icon=(
        str(icon_win) if sys.platform == "win32" and icon_win.exists()
        else str(icon_mac) if sys.platform == "darwin" and icon_mac.exists()
        else None
    ),
)

if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="Girgitton.app",
        icon=str(icon_mac) if icon_mac.exists() else None,
        bundle_identifier="com.girgitton.app",
        info_plist={
            "CFBundleURLTypes": [
                {
                    "CFBundleURLName": "Girgitton",
                    "CFBundleURLSchemes": ["girgitton"],
                }
            ],
            "NSHighResolutionCapable": "True",
        },
    )
