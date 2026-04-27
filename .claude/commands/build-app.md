---
description: Build desktop app .exe / .app / .bin via PyInstaller
---

Build the Girgitton Desktop App for the current platform:

1. Ensure `pip install -e ".[app,build]"`
2. `pyinstaller scripts/package.spec --clean --noconfirm`
3. Verify output in `dist/Girgitton.*`
4. Test launch — expect login frame
5. SHA256 checksum for release
