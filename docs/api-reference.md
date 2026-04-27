# HTTP API Reference

> Asos URL: `https://<your-app>.railway.app` yoki lokal `http://127.0.0.1:8080`

Barcha imzolangan endpointlar HMAC-SHA256 talab qiladi:

```
X-Signature: <hex digest>
X-Timestamp: <unix seconds>
```

Imzo formuli: `HMAC(api_secret, f"{timestamp}." + raw_body)`.

---

## `GET /health`

Auth: **yo'q** (Railway healthcheck).

```http
HTTP/1.1 200 OK
{"ok": true, "service": "girgitton", "version": "3.0.0"}
```

---

## `GET /auto-pair`

Auth: **faqat 127.0.0.1**. Lokal Desktop App uchun avtomatik credentials.

Response:

```json
{
  "ok": true,
  "credentials": {"api_id": 12345, "api_hash": "...", "bot_token": "..."},
  "groups": [{"id": -1001, "title": "My Group"}],
  "api_secret": "..."
}
```

---

## `POST /pair`

Auth: **pair code** (kodning o'zi). One-time use.

Request:

```json
{ "code": "ABC123" }
```

Success response (200):

```json
{
  "ok": true,
  "credentials": {"api_id": 12345, "api_hash": "...", "bot_token": "..."},
  "group": {"id": -1001, "title": "My Group"},
  "groups": [{"id": -1001, "title": "My Group"}],
  "api_secret": "..."
}
```

Xatolar: 400 (yaroqsiz JSON), 403 (kod yaroqsiz/muddati o'tgan).

---

## `GET /groups`

Auth: **(hozircha) ochiq** (faqat o'qish, sirsiz). Kelajakda HMAC.

```json
{ "ok": true, "groups": [{"id": -1001, "title": "My Group"}] }
```

---

## `POST /status`

Auth: **HMAC**. Har 5 soniyada Desktop App yuboradi.

Request body:

```json
{
  "user_id": 5567796386,
  "chat_id": -1001,
  "batch": 3,
  "total": 10,
  "speed": 1.42
}
```

Response: `{"ok": true}`.

Xatolar: 401 (HMAC), 400 (DTO).

---

## `GET /task`

Auth: **HMAC**. Har 5 soniyada Desktop App tekshiradi.

Query: `?user_id=<int>`

Response:

```json
{ "action": "stop" }     // yoki: { "action": null }
```

Xatolar: 401 (HMAC), 400 (user_id yo'q).

---

## Rate limits

| Tahdid                     | Limit               |
| -------------------------- | ------------------- |
| Per-IP (barcha endpointlar)| 60 / min            |
| /pair (per-user)           | 10 / min            |
