#!/usr/bin/env python3
"""PyInstaller build helper.

Foydalanish:
    python scripts/build_app.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "scripts" / "package.spec"
DIST = ROOT / "dist"
BUILD = ROOT / "build"


def main() -> int:
    if not SPEC.exists():
        print(f"Spec topilmadi: {SPEC}", file=sys.stderr)
        return 1

    for d in (DIST, BUILD):
        if d.exists():
            shutil.rmtree(d)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        str(SPEC),
        "--clean",
        "--noconfirm",
    ]
    print(f"$ {' '.join(cmd)}")
    rc = subprocess.call(cmd, cwd=ROOT)
    if rc != 0:
        print("Build muvaffaqiyatsiz.", file=sys.stderr)
        return rc

    print("\n✅ Build tugadi:")
    for entry in DIST.iterdir():
        print(f"  - {entry.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
