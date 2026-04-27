# Architecture — Girgitton v3.0

## High-level diagram

```mermaid
flowchart LR
    subgraph local[Lokal kompyuter]
        FS[(Media papka<br/>~/Photos)]
        APP[Desktop App<br/>CustomTkinter]
        ENG[Upload Engine<br/>3 worker pool]
        APP -->|tanlash| FS
        APP -->|run| ENG
    end

    subgraph rail[Railway]
        BOT[Telegram Bot<br/>Telethon]
        API[HTTP API<br/>aiohttp + HMAC]
        REDIS[(Redis<br/>fallback: JSON)]
        BOT --> REDIS
        API --> REDIS
    end

    subgraph tg[Telegram]
        GROUP[Maqsadli guruh]
    end

    APP -->|HTTPS+HMAC<br/>/pair, /status, /task| API
    ENG -->|MTProto<br/>send_file x2| GROUP
    BOT -->|/pair, /status, /stop| GROUP
```

## Yuborish algoritmi (single-upload, dual-send)

```mermaid
sequenceDiagram
    participant U as User
    participant W as Worker
    participant TG as Telegram

    U->>W: Boshlash (papka tanlangan)
    Note over W: Skaner → 5 tadan batch
    loop Har 5 ta fayl uchun
        W->>TG: upload_file × 5  (1 marta)
        TG-->>W: InputDocument list
        W->>TG: send_file (force_document=False)  ← media album
        Note over W: 1s pauza
        W->>TG: send_file (force_document=True)   ← document album
        Note over W: 2s pauza, keyingi batch
    end
```

## Komponent qatlamlari

| Qatlam       | Modul                                           | Vazifa                                                       |
| ------------ | ----------------------------------------------- | ------------------------------------------------------------ |
| `core`       | `config`, `models`, `errors`, `logging_setup`   | Domen-pure: ramka-mustaqil DTO va konfiguratsiya             |
| `shared`     | `crypto`, `media`, `repositories`               | Bot va App o'rtasida umumiy yordamchilar                     |
| `storage`    | `base`, `redis_store`, `json_store`, `factory`  | `StorageRepository` Protocol + ikki adapter                  |
| `bot`        | `client`, `handlers/*`, `api/*`                 | Telethon hodisalari + aiohttp HTTP API                       |
| `app`        | `gui/*`, `upload/*`, `api_client`, `config_store` | CustomTkinter GUI + 3-worker upload engine                |
| `platform`   | `windows`, `macos`                              | OS-specific kod (deep link, keyring fallback)                |

## Data flow — pair flow

```mermaid
sequenceDiagram
    participant Owner as Foydalanuvchi
    participant Bot as Bot (TG)
    participant API as HTTP API
    participant Storage as Redis/JSON
    participant App as Desktop App

    Owner->>Bot: /pair (guruhda)
    Bot->>Storage: save pair_code (TTL 5m)
    Bot-->>Owner: kod ABC123 + deep link
    Owner->>App: kod ABC123 ni kiritadi
    App->>API: POST /pair {code: ABC123}
    API->>Storage: getdel pair_code
    API-->>App: credentials (api_id, hash, bot_token, secret)
    App->>App: Fernet encrypt → ~/.girgitton/credentials.enc
    App->>API: POST /status (HMAC) — har 5s
    Note over App: Upload boshlanadi
```

## Worker pool va rotatsiya

3 mezonli rotatsiya har worker uchun:

1. **Soni** — har `ROTATE_AFTER_N_BATCHES` (15) batchdan keyin sessiya yangilanadi
2. **Vaqt** — `ROTATE_AFTER_SECONDS` (300) oshib ketsa
3. **Tezlik** — oxirgi 3 batch o'rtacha tezligi `SPEED_DROP_THRESHOLD_MB_S` (0.10) dan past

Throttle aniqlanganda (oxirgi batch < `THROTTLE_SPEED_LIMIT_MB_S`):

- GUI dialog ochiladi (countdown + manual retry)
- `THROTTLE_WAIT_SECONDS` (1800) kutiladi
- Sessiya majburiy yangilanadi
