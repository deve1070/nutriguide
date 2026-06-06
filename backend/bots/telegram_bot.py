"""
Telegram Bot — Webhook Mode

Flow:
1. User sends message to bot
2. Telegram POSTs update to /webhooks/telegram
3. We parse it, call bot_service, send response via Telegram API
4. Telegram delivers the response to the user

Setup:
1. Create bot with @BotFather → get token
2. Run ngrok: ngrok http 8002
3. Register webhook: POST /webhooks/telegram/setup
"""

import hmac
from typing import Optional

import httpx

from backend.config import get_settings

settings = get_settings()

TELEGRAM_API = f"https://api.telegram.org/bot{settings.telegram_bot_token}"


# ── Telegram API helpers ──────────────────────────────


async def send_message(
    chat_id: int | str,
    text: str,
    parse_mode: str = "Markdown",
):
    """Send a message to a Telegram chat"""
    # Telegram Markdown has a 4096 char limit per message
    chunks = _split_message(text, 4000)

    async with httpx.AsyncClient() as client:
        for chunk in chunks:
            await client.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": parse_mode,
                },
            )


async def send_typing(chat_id: int | str):
    """Show 'typing...' indicator while processing"""
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{TELEGRAM_API}/sendChatAction",
            json={
                "chat_id": chat_id,
                "action": "typing",
            },
        )


async def set_webhook(url: str, secret: str) -> dict:
    """Register our webhook URL with Telegram"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{TELEGRAM_API}/setWebhook",
            json={
                "url": url,
                "secret_token": secret,
                "allowed_updates": ["message"],
                "drop_pending_updates": True,
            },
        )
        return response.json()


async def delete_webhook() -> dict:
    """Remove the webhook (switch to polling mode)"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{TELEGRAM_API}/deleteWebhook")
        return response.json()


async def get_webhook_info() -> dict:
    """Check current webhook status"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{TELEGRAM_API}/getWebhookInfo")
        return response.json()


# ── Webhook verification ──────────────────────────────


def verify_telegram_secret(
    secret_header: Optional[str],
    expected_secret: str,
) -> bool:
    """
    Verify the X-Telegram-Bot-Api-Secret-Token header.
    Telegram sends this with every webhook request if you set secret_token.
    """
    if not expected_secret:
        return True  # no secret configured, skip verification
    if not secret_header:
        return False
    return hmac.compare_digest(secret_header, expected_secret)


# ── Update parsing ────────────────────────────────────


def parse_update(update: dict) -> Optional[dict]:
    """
    Extract the relevant fields from a Telegram update.
    Returns None if the update has no text message.
    """
    message = update.get("message")
    if not message:
        return None

    text = message.get("text")
    if not text:
        return None

    chat = message.get("chat", {})
    sender = message.get("from", {})

    return {
        "chat_id": chat.get("id"),
        "user_id": sender.get("id"),
        "username": sender.get("username"),
        "first_name": sender.get("first_name", ""),
        "last_name": sender.get("last_name", ""),
        "text": text,
        "message_id": message.get("message_id"),
    }


def get_display_name(parsed: dict) -> str:
    first = parsed.get("first_name", "")
    last = parsed.get("last_name", "")
    return f"{first} {last}".strip() or parsed.get("username") or "Telegram User"


# ── Helpers ───────────────────────────────────────────


def _split_message(text: str, limit: int) -> list[str]:
    """Split long messages into chunks that fit Telegram's limit"""
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break
        # Split at newline if possible
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks
