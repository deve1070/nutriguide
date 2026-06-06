"""
WhatsApp Bot — Twilio Sandbox

Flow:
1. User sends message to Twilio WhatsApp sandbox number
2. Twilio POSTs to /webhooks/whatsapp
3. We parse it, call bot_service, return TwiML response
4. Twilio delivers our response to the user

Setup:
1. Go to console.twilio.com → Messaging → Try it out → WhatsApp
2. Follow sandbox setup (send join code to +1 415 523 8886)
3. Set webhook URL: https://your-ngrok-url/webhooks/whatsapp
4. Add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN to .env
"""

import base64
import hashlib
import hmac
from typing import Optional

import httpx

from backend.config import get_settings

settings = get_settings()

TWILIO_API = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}"


# ── Message sending ───────────────────────────────────


async def send_whatsapp_message(to: str, body: str):
    """
    Send a WhatsApp message via Twilio REST API.
    `to` should be in format: whatsapp:+251912345678
    """
    # WhatsApp has a 1600 char limit per message
    chunks = _split_message(body, 1500)

    async with httpx.AsyncClient() as client:
        for chunk in chunks:
            await client.post(
                f"{TWILIO_API}/Messages.json",
                data={
                    "From": settings.twilio_whatsapp_number,
                    "To": to,
                    "Body": chunk,
                },
                auth=(settings.twilio_account_sid, settings.twilio_auth_token),
            )


# ── Webhook verification ──────────────────────────────


def verify_twilio_signature(
    auth_token: str,
    signature: str,
    url: str,
    params: dict,
) -> bool:
    """
    Verify Twilio's X-Twilio-Signature header.
    Twilio signs every webhook request with your auth token.
    https://www.twilio.com/docs/usage/webhooks/webhooks-security
    """
    # Sort params and concatenate with URL
    s = url + "".join(f"{k}{v}" for k, v in sorted(params.items()))
    mac = hmac.new(
        auth_token.encode("utf-8"),
        s.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    computed = base64.b64encode(mac).decode("utf-8")
    return hmac.compare_digest(computed, signature)


# ── TwiML response ────────────────────────────────────


def twiml_response(body: str) -> str:
    """
    Build a TwiML XML response.
    Twilio reads this and delivers the message to the user.
    We use this for synchronous responses (faster than async API call).
    """
    # Escape XML special characters
    safe_body = (
        body.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        # Remove Markdown since WhatsApp uses different formatting
        .replace("*", "")
        .replace("_", "")
        .replace("`", "")
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{safe_body}</Message>
</Response>"""


def twiml_empty() -> str:
    """Empty TwiML — used when we handle the response asynchronously"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<Response></Response>"""


# ── Update parsing ────────────────────────────────────


def parse_whatsapp_update(form_data: dict) -> Optional[dict]:
    """
    Parse incoming Twilio WhatsApp webhook form data.
    Returns None if not a valid text message.
    """
    body = form_data.get("Body", "").strip()
    from_num = form_data.get("From", "")  # e.g. whatsapp:+251912345678
    profile_name = form_data.get("ProfileName", "")

    if not body or not from_num:
        return None

    # Strip the "whatsapp:" prefix for storage
    phone = from_num.replace("whatsapp:", "")

    return {
        "from": from_num,  # full "whatsapp:+..." for sending back
        "phone": phone,  # just the number for user ID
        "profile_name": profile_name,
        "text": body,
        "num_media": int(form_data.get("NumMedia", 0)),
    }


# ── Helpers ───────────────────────────────────────────


def format_for_whatsapp(text: str) -> str:
    """
    Convert Markdown-ish formatting to WhatsApp formatting.
    WhatsApp uses *bold*, _italic_, ~strikethrough~
    """
    # Our bot uses *bold* already — WhatsApp supports that
    # Remove unsupported markdown
    return text.replace("`", "").replace("~~", "~")


def _split_message(text: str, limit: int) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks
