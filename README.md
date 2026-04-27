# 🐈 Girgitton v3.0

> Lokal papkadan rasm/video fayllarni Telegram guruhiga **5 tadan** album sifatida (avval **media preview**, keyin **fayl/document**) navbatma-navbat yuboruvchi tizim. **3 worker** parallel yuklash bilan tezlikni oshiradi, throttling sodir bo'lganda avtomatik tiklanadi.

## Komponentlar

| Komponent       | Joylashuv                      | Vazifasi                                       |
| --------------- | ------------------------------ | ---------------------------------------------- |
| **Bot**         | `src/girgitton/bot/` (Railway) | Telethon + aiohttp HTTP API                    |
| **Desktop App** | `src/girgitton/app/` (lokal)   | CustomTkinter GUI + 3-worker upload engine     |

## Tezkor start

```bash
# 1) Bog'liqliklar
python -m venv .venv && source .venv/Scripts/activate    # Win: .venv\Scripts\activate
pip install -e ".[app,dev]"

# 2) Sirlar
cp .env.example .env && $EDITOR .env

# 3) Bot
python -m girgitton.bot

# 4) Boshqa terminal: Desktop App
python -m girgitton.app
```

## Hujjatlar

- [project.md](project.md) — to'liq arxitektura
- [jarayon.txt](jarayon.txt) — bosqichma-bosqich qurish rejasi
- [bajarildi.txt](bajarildi.txt) — bajarilgan bosqichlar
- [docs/architecture.md](docs/architecture.md) — diagrammalar
- [docs/security.md](docs/security.md) — tahdid modeli
- [docs/onboarding.md](docs/onboarding.md) — yangi foydalanuvchi

## Verify

```bash
ruff check src/ tests/
mypy src/girgitton
pytest -q
bandit -r src/ -ll
```

## Litsenziya

MIT
