"""/help, /download handlerlari (/start enrollment.py'da)."""

from __future__ import annotations

import os

from telethon import TelegramClient, events

from girgitton.bot.handlers.decorators import EventT, safe_handler


def register_help(client: TelegramClient) -> None:
    github_repo = os.getenv("GITHUB_REPO", "Navkariya/girgitton")

    @client.on(events.NewMessage(pattern=r"^/help(@\w+)?$"))
    @safe_handler
    async def cmd_help(event: EventT) -> None:
        from girgitton.bot.handlers.enrollment import WELCOME_TEXT

        await event.reply(WELCOME_TEXT, parse_mode="md")

    @client.on(events.NewMessage(pattern=r"^/download(@\w+)?$"))
    @safe_handler
    async def cmd_download(event: EventT) -> None:
        base = f"https://github.com/{github_repo}/releases/latest/download"
        releases = f"https://github.com/{github_repo}/releases/latest"
        await event.reply(
            "💻 **Girgitton Desktop App** — yuklab olish\n\n"
            f"🪟 [Windows (.exe)]({base}/Girgitton_Windows.exe)\n"
            f"🍎 [macOS (.zip)]({base}/Girgitton_macOS.zip)\n"
            f"🐧 [Linux (.bin)]({base}/Girgitton_Linux.bin)\n\n"
            f"📋 [Barcha versiyalar va SHA256]({releases})\n\n"
            "**Ishlatish:**\n"
            "1. Operatsion tizimingizga mos faylni yuklang\n"
            "2. Faylni ochib App ni ishga tushiring\n"
            "3. Avtomatik Telegram orqali ulanish so'raydi\n"
            "4. Guruhlarda `/here` yuborib, papkalarni tanlang",
            parse_mode="md",
        )
