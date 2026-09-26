# Cloud Telegram Bot (Render)

This deployment runs the Telegram command bot in the cloud using a Telegram webhook.

## Architecture

Telegram -> HTTPS webhook -> Render web service -> Personal Style Agent command handlers -> Telegram reply

The local polling process is no longer required after the webhook is active.

## Deploy

1. Sign in to Render.
2. Create a new Blueprint from this GitHub repository, or create a Web Service using the repository.
3. Render reads `render.yaml`.
4. Set these secret environment variables in Render:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
5. Render generates:
   - `TELEGRAM_WEBHOOK_SECRET`
   - `CLOUD_ADMIN_SECRET`
6. Deploy the service.

The app uses Render's `RENDER_EXTERNAL_URL` to register:

`https://<service>.onrender.com/telegram/webhook`

with Telegram automatically when the service starts.

## Health check

Open:

`https://<service>.onrender.com/health`

Expected:

`{"ok": true}`

## Telegram commands

- `/today`
- `/report`
- `/wardrobe`
- `/help`

## Important

Once Telegram has an active webhook, Telegram's `getUpdates` long polling API cannot be used for the same bot at the same time. The cloud webhook replaces the need to keep `python telegram_bot/bot.py` running locally.

Secrets must only be stored in Render/GitHub Secrets or local ignored .env files.
