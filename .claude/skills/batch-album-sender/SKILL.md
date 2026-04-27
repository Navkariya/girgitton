---
name: batch-album-sender
description: Pattern for sending Telegram media as media-album then document-album using a single upload
---

# Batch Album Sender (single-upload, dual-send)

Telegram can send a list of `InputDocument` objects as either a media album (preview) or a document album. Once a file is uploaded via `client.upload_file()`, the resulting `InputFile` can be referenced from `send_file` repeatedly without re-uploading.

## Canonical pattern

```python
from telethon import TelegramClient
from telethon.tl.types import InputDocument

async def send_batch(
    client: TelegramClient,
    chat_id: int,
    files: list[Path],
    idx: int,
    total: int,
    delay_between_steps: float = 1.0,
) -> None:
    # Step 1: upload all 5 files ONCE
    uploaded = [await client.upload_file(str(f)) for f in files]

    # Step 2: send as media album (preview)
    media_caption = f"📸 Qism {idx}/{total} — Media ({len(files)} ta)"
    await client.send_file(
        chat_id,
        uploaded,
        caption=[media_caption] + [""] * (len(files) - 1),
        force_document=False,
    )

    await asyncio.sleep(delay_between_steps)

    # Step 3: same uploaded files, document album
    doc_caption = f"📁 Qism {idx}/{total} — Documents ({len(files)} ta)"
    await client.send_file(
        chat_id,
        uploaded,
        caption=[doc_caption] + [""] * (len(files) - 1),
        force_document=True,
    )
```

## Why this works

`client.upload_file()` returns an `InputFile` (small file) or `InputFileBig` (large file) which references the upload session on Telegram servers. `send_file` accepting an `InputFile` skips re-upload — it just creates the message with that media reference.

## Rules

1. **Always media first, document second** — UX expectation.
2. **Single upload per batch of 5** — halves bandwidth.
3. **First caption only** — Telegram albums use only the first item's caption.
4. **Respect `DELAY_BETWEEN_STEPS`** — avoid rate spikes inside a single batch.
5. **`DELAY_BETWEEN_BATCHES`** between consecutive 5-tuples (different worker, same chat).

## Failure modes

- `FloodWaitError` mid-step → retry the *whole* batch from upload (refs may expire after long waits).
- Album size exceeds 50 MB total → reduce BATCH_SIZE or fall back to per-file send.
- File reference expired (rare) → re-upload and retry.
