# Security — Girgitton v3.0

## Tahdid modeli (STRIDE)

| Kategoriya      | Tahdid                                              | Mitigation                                              |
| --------------- | --------------------------------------------------- | ------------------------------------------------------- |
| **Spoofing**    | Soxta App API ga ulanmoqchi bo'ladi                 | HMAC-SHA256 imzo + per-pair token                       |
| **Tampering**   | Request body o'zgartirildi                          | HMAC body bilan birga imzolanadi                        |
| **Repudiation** | Foydalanuvchi /pair ni rad etadi                    | Storage da `user_id` saqlanadi, log oqimida             |
| **Info disc.**  | Bot tokeni log/exception orqali oqib chiqadi        | `SecretStr.__repr__ == "***"` + `SecretFilter`          |
| **DoS**         | API ga juda ko'p request                            | Per-IP 60/min rate limit, per-user pair 10/min          |
| **Elev. priv.** | Boshqa foydalanuvchi `/pair` yuboradi               | `@allowed_only` (Owner + ALLOWED_USERS + ACL list)      |

## HMAC imzo formati

```
X-Signature: hex(HMAC_SHA256(secret, f"{timestamp}." + body))
X-Timestamp: <unix_seconds>
```

Tekshirish:
- `hmac.compare_digest` — timing-safe
- `abs(now - timestamp) ≤ 60s` — replay-protection

## Pair code

- Alphabet: `ABCDEFGHJKLMNPQRSTUVWXYZ23456789` (`0/O/1/I` shubhasiz)
- Length: 6 (≈ 32^6 ≈ 10⁹ kombinatsiya)
- TTL: 5 daqiqa
- Brute-force lock: per-user 10 urinish/daqiqa
- One-time: `getdel` atomik

## Fernet (lokal credentials)

```
~/.girgitton/credentials.enc   ← shifrlangan blob
~/.girgitton/credentials.key   ← Fernet kalit (faqat keyring yo'q bo'lsa)
```

Kalit prioriteti:
1. **Keyring** (Win DPAPI / macOS Keychain / Linux SecretService)
2. **Fayl fallback** (0600 permission)

## Pre-commit checklist

- [ ] `bandit -r src/ -ll` — zero high
- [ ] Hech qanday `print()` (faqat `logger`)
- [ ] Hech qanday hardcoded sirlar (regex skan)
- [ ] HMAC `compare_digest`
- [ ] Har route DTO orqali validatsiya
- [ ] Rate limit har stateful endpointda

## Incident response

| Hodisa                            | Action                                                 |
| --------------------------------- | ------------------------------------------------------ |
| Bot tokeni oqib ketdi             | @BotFather dan revoke + Railway env yangilash + redeploy |
| Pair code zo'rlash urinishlari    | Rate-limit ushlaydi, log da audit trail               |
| Lokal credentials.enc o'g'irlandi | Fernet key OS keyring da — qiymat foydasiz             |
| Redis o'chgan                     | JSON fallback avtomatik (logda warning)                |
