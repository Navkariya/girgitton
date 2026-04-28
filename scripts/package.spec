# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — Girgitton Desktop App.

Default: --onefile (portable .exe).
Inno Setup uchun --onedir kerak. Buni env var bilan o'tkazamiz:
    BUILD_MODE=onedir pyinstaller scripts/package.spec --clean --noconfirm
"""

import os
import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent
BUILD_MODE = os.environ.get("BUILD_MODE", "onefile").lower()  # onefile | onedir

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
        "girgitton.app.gui.connect_dialog",
        "girgitton.app.gui.main_frame",
        "girgitton.app.gui.throttle_dialog",
        "girgitton.app.gui.server_dialog",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=["pytest", "redis"],
    noarchive=False,
)

pyz = PYZ(a.pure)

_icon = (
    str(icon_win) if sys.platform == "win32" and icon_win.exists()
    else str(icon_mac) if sys.platform == "darwin" and icon_mac.exists()
    else None
)

if BUILD_MODE == "onedir":
    # ─── --onedir: dist/Girgitton/{Girgitton.exe, _internal/, ...}
    # Inno Setup ushbu papkadan ishlaydi (installer manbai)
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="Girgitton",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,  # Inno Setup o'zi compress qiladi
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=True,
        target_arch=None,
        icon=_icon,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name="Girgitton",
    )
else:
    # ─── --onefile (default): bitta `.exe` (portable)
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
        icon=_icon,
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
