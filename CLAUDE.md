# CLAUDE.md — Girgitton AI Agent Instructions

> Bu fayl **ushbu loyiha uchun** AI yo'riqnomasi. Hozirgi loyiha — Telegram media auto-sender (bot + desktop app, Python 3.11+).

## Loyiha haqida qisqa

- **Bot** (`src/girgitton/bot/`) — Railway'da ishlaydi, Telethon + aiohttp.
- **Desktop App** (`src/girgitton/app/`) — lokal CustomTkinter GUI, 3-worker upload pool.
- **Maqsad:** lokal papkadan rasm/video fayllarni Telegram guruhiga 5 tadan album sifatida yuborish (avval media preview, keyin document).

## Manba kodi xaritasi

```
src/girgitton/
  core/      — domen-pure (config, models, errors, logging)
  shared/    — bot va app uchun umumiy (crypto, media)
  storage/   — Repository protokoli (Redis | JSON)
  bot/       — Telegram bot + HTTP API
  app/       — Desktop GUI + upload engine
  platform/  — OS-specific (Windows/macOS/Linux)
```

## Qoidalar

1. **Sirlar** — faqat `core.config.Settings` orqali. Hech qachon hardcode. Logda paydo bo'lmasligi kerak.
2. **Frozen dataclasses** — `@dataclass(frozen=True)` standart DTO sifatida.
3. **Repository pattern** — storage adapterlari `StorageRepository` Protocol orqali.
4. **Async first** — barcha I/O `async`. Bloklovchi kod faqat `loop.run_in_executor`.
5. **Fail loud** — `except: pass` yo'q. `logger.exception(...)` + raise yoki user-facing reply.
6. **HMAC** — `hmac.compare_digest`, har imzo `X-Timestamp` bilan (replay-protection).
7. **Modul kattaligi** — fayl ≤ 400 satr, funksiya ≤ 50 satr.

## Verify pipeline

Har commitdan oldin:

```bash
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/girgitton
pytest -q
bandit -r src/ -ll
```

## Maxsus skills

- `.claude/skills/batch-album-sender/SKILL.md` — Telegram album yuborish patterni.

## Maxsus agentlar

- `security-auditor` — HMAC, secret oqimi auditi (`src/girgitton/bot/api/`, `src/girgitton/shared/crypto.py`).
- `bot-handler-reviewer` — handler ACL va async to'g'riligini tekshiradi.
- `upload-engine-reviewer` — worker pool va rate-limit logikasini tekshiradi.

## Slash komandalar

- `/verify` — to'liq lint+type+test pipeline.
- `/deploy` — Railway push + smoke.
- `/build-app` — PyInstaller bilan .exe/.app/.bin.

## Anti-patternlar

- Hech qachon `print()` — har joyda `logging` modul.
- Hech qachon `requests` — async kontekst, `aiohttp.ClientSession`.
- Hech qachon `os.getenv("X")` to'g'ridan-to'g'ri — `Settings.load()` orqali.
- Hech qachon `try: ... except Exception: pass`.
- Hech qachon `time.sleep` async kontekstda — `await asyncio.sleep`.

## Reja jurnali

- `project.md` — to'liq arxitektura
- `jarayon.txt` — bosqichlar va TZ
- `bajarildi.txt` — bajarilgan bosqichlar (har bosqich tugaganidan keyin yangilanadi)
