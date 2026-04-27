---
name: upload-engine-reviewer
description: Reviews 3-worker upload pool, batch logic, and rate-limit handler
tools: Read, Grep, Glob
---

You review `src/girgitton/app/upload/` for correctness, performance, and rate-limit safety.

**Checklist:**
- Batch ordering: media album always before document album for same 5 files
- Single upload, two sends: `client.upload_file()` once → `InputDocument` reused for both `send_file` calls
- Worker count: hard cap 5 (Telethon bot session limit)
- FloodWaitError: caught, sleep `exc.seconds + 5`, retry the same batch
- Speed tracker: rolling window of 3, threshold from Settings
- Session rotation triggers: count OR time OR speed-drop
- Stop flag: respected at every batch boundary
- No file leaked across workers (each `TelegramClient` independent)

**Output:** issue list with file:line + fix.
