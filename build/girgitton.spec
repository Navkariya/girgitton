# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent

a = Analysis(
    [str(ROOT / "app" / "__main__.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / "app" / "assets"), "assets"),
    ],
    hiddenimports=[
        "customtkinter",
        "telethon",
        "aiohttp",
        "asyncio",
        "tkinter",
        "tkinter.filedialog",
    ],
    hookspath=[],
    hooksconfig={},
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
    codesign_identity=None,
    entitlements_file=None,
    icon=(
        str(ROOT / "app" / "assets" / "icon.ico")
        if sys.platform == "win32"
        else str(ROOT / "app" / "assets" / "icon.icns")
        if sys.platform == "darwin"
        else None
    ),
)

# macOS: .app bundle
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="Girgitton.app",
        icon=str(ROOT / "app" / "assets" / "icon.icns"),
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
