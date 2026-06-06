# NutriGuide Bot Setup

NutriGuide works on Telegram and WhatsApp. Both bots use the same RAG engine and respect each user's health profile.

---

## Telegram Setup

### 1. Create your bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a name: `NutriGuide`
4. Choose a username: `nutriguide_yourname_bot`
5. Copy the **bot token**

### 2. Configure environment

Add to your `.env` / docker-compose:

```env
TELEGRAM_BOT_TOKEN=your-token-here
TELEGRAM_WEBHOOK_SECRET=any-random-string-you-choose
PUBLIC_URL=https://your-ngrok-or-render-url
```

### 3. Start ngrok (local dev)

```bash
ngrok http 8002
```

Copy the `https://abc123.ngrok.io` URL and set it as `PUBLIC_URL`.

### 4. Register the webhook

```bash
curl -X POST http://localhost:8002/webhooks/telegram/setup
```

You should see:

```json
{
  "webhook_url": "https://abc123.ngrok.io/webhooks/telegram",
  "telegram_response": { "ok": true, "result": true }
}
```

### 5. Test it

Open your bot in Telegram and send:

```
/start
```

---

## WhatsApp Setup (Twilio Sandbox)

### 1. Create a Twilio account

Go to [console.twilio.com](https://console.twilio.com) and sign up for free.

### 2. Join the WhatsApp sandbox

1. Go to **Messaging → Try it out → Send a WhatsApp message**
2. You'll see a number like `+1 415 523 8886` and a join code like `join bright-example`
3. Send that join message from your WhatsApp to activate the sandbox

### 3. Configure the webhook

In Twilio console → **Messaging → Try it out → WhatsApp sandbox settings**:

Set **When a message comes in** to:

```
https://your-ngrok-or-render-url/webhooks/whatsapp
```

HTTP method: `POST`

### 4. Configure environment

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

### 5. Test it

Send a message to the sandbox number from WhatsApp. You should get a NutriGuide response.

---

## Bot Commands

Both bots support:

| Command          | Action                       |
| ---------------- | ---------------------------- |
| `/start` or `hi` | Welcome message              |
| `/help`          | Show command list            |
| `/profile`       | Show your health profile     |
| `/mealplan`      | Get today's meal suggestions |
| Any text         | RAG food recommendation      |

---

## Production Deployment (Render)

For Render deployment, set these environment variables in the Render dashboard:

```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_WEBHOOK_SECRET=...
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
PUBLIC_URL=https://nutriguide-api.onrender.com
```

After deploying, register the Telegram webhook:

```bash
curl -X POST https://nutriguide-api.onrender.com/webhooks/telegram/setup
```

Update Twilio webhook URL to:

```
https://nutriguide-api.onrender.com/webhooks/whatsapp
```

---

## Check Status

```bash
curl http://localhost:8002/webhooks/status
```

Returns:

```json
{
  "telegram": { "configured": true, "webhook_info": { ... } },
  "whatsapp":  { "configured": true, "number": "whatsapp:+14155238886" }
}
```
