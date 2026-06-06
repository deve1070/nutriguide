"""
Webhook endpoints for Telegram and WhatsApp bots.

Telegram:  POST /webhooks/telegram
WhatsApp:  POST /webhooks/whatsapp
Setup:     POST /webhooks/telegram/setup   (register webhook with Telegram)
Status:    GET  /webhooks/status           (check both bots)
"""

import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from backend.bots.telegram_bot import (
    delete_webhook,
    get_display_name,
    get_webhook_info,
    parse_update,
    set_webhook,
    verify_telegram_secret,
)
from backend.bots.telegram_bot import (
    send_message as tg_send,
)
from backend.bots.telegram_bot import (
    send_typing as tg_typing,
)
from backend.bots.whatsapp_bot import (
    format_for_whatsapp,
    parse_whatsapp_update,
    twiml_empty,
    twiml_response,
    verify_twilio_signature,
)
from backend.config import get_settings
from backend.database import get_db
from backend.services.bot_service import (
    get_or_create_bot_user,
    process_message,
)

settings = get_settings()
router = APIRouter(prefix="/webhooks", tags=["Bots"])


# ── Telegram ──────────────────────────────────────────


@router.post(
    "/telegram",
    summary="Telegram webhook — receives updates from Telegram",
    include_in_schema=False,  # hide from public docs
)
async def telegram_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_telegram_bot_api_secret_token: Optional[str] = Header(default=None),
):
    # Verify the request is from Telegram
    if not verify_telegram_secret(
        x_telegram_bot_api_secret_token,
        settings.telegram_webhook_secret,
    ):
        raise HTTPException(status_code=403, detail="Invalid Telegram secret")

    update = await request.json()

    # Parse the incoming update
    parsed = parse_update(update)
    if not parsed:
        return {"ok": True}  # ignore non-text updates silently

    chat_id = parsed["chat_id"]
    user_id = parsed["user_id"]
    text = parsed["text"]
    username = parsed.get("username")
    name = get_display_name(parsed)

    # Show typing indicator immediately
    asyncio.create_task(tg_typing(chat_id))

    # Get or create bot user
    bot_user = get_or_create_bot_user(
        db=db,
        platform="telegram",
        platform_user_id=str(user_id),
        platform_username=username,
        display_name=name,
    )

    # Process message through RAG engine
    response_text = process_message(db=db, bot_user=bot_user, message=text)

    # Send response back to Telegram
    await tg_send(chat_id, response_text)

    return {"ok": True}


@router.post(
    "/telegram/setup",
    summary="Register NutriGuide webhook URL with Telegram",
    description=(
        "Call this once after deployment to tell Telegram where to send updates. "
        "Requires PUBLIC_URL to be set in your environment."
    ),
)
async def setup_telegram_webhook():
    if not settings.telegram_bot_token:
        raise HTTPException(status_code=503, detail="TELEGRAM_BOT_TOKEN not configured")

    if not settings.public_url:
        raise HTTPException(
            status_code=400,
            detail="PUBLIC_URL not set. Set it to your ngrok URL or Render URL.",
        )

    webhook_url = f"{settings.public_url.rstrip('/')}/webhooks/telegram"
    result = await set_webhook(webhook_url, settings.telegram_webhook_secret)

    return {
        "webhook_url": webhook_url,
        "telegram_response": result,
    }


@router.delete(
    "/telegram/setup",
    summary="Remove the Telegram webhook",
)
async def remove_telegram_webhook():
    result = await delete_webhook()
    return result


# ── WhatsApp ──────────────────────────────────────────


@router.post(
    "/whatsapp",
    summary="WhatsApp webhook — receives messages from Twilio",
    response_class=PlainTextResponse,
    include_in_schema=False,
)
async def whatsapp_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_twilio_signature: Optional[str] = Header(default=None),
):
    # Parse form data (Twilio sends application/x-www-form-urlencoded)
    form_data = dict(await request.form())

    # Verify Twilio signature
    if settings.twilio_auth_token and x_twilio_signature:
        url = str(request.url)
        if not verify_twilio_signature(
            settings.twilio_auth_token,
            x_twilio_signature,
            url,
            form_data,
        ):
            return PlainTextResponse(
                content=twiml_empty(),
                media_type="application/xml",
                status_code=403,
            )

    parsed = parse_whatsapp_update(form_data)
    if not parsed:
        return PlainTextResponse(
            content=twiml_empty(),
            media_type="application/xml",
        )

    phone = parsed["phone"]
    from_number = parsed["from"]
    text = parsed["text"]
    profile_name = parsed["profile_name"]

    # Get or create bot user
    bot_user = get_or_create_bot_user(
        db=db,
        platform="whatsapp",
        platform_user_id=phone,
        platform_username=phone,
        display_name=profile_name or phone,
    )

    # Process through RAG engine
    response_text = process_message(db=db, bot_user=bot_user, message=text)

    # Format for WhatsApp and return as TwiML
    formatted = format_for_whatsapp(response_text)
    return PlainTextResponse(
        content=twiml_response(formatted),
        media_type="application/xml",
    )


# ── Status ────────────────────────────────────────────


@router.get(
    "/status",
    summary="Check bot configuration status",
)
async def bot_status():
    telegram_info = None
    if settings.telegram_bot_token:
        try:
            telegram_info = await get_webhook_info()
        except Exception:
            telegram_info = {"error": "Could not reach Telegram API"}

    return {
        "telegram": {
            "configured": bool(settings.telegram_bot_token),
            "webhook_info": telegram_info,
        },
        "whatsapp": {
            "configured": bool(settings.twilio_account_sid),
            "number": settings.twilio_whatsapp_number or "not set",
        },
    }
