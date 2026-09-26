# Telegram Bot

## 1. Create the bot

Open Telegram and talk to **@BotFather**.

Use:

```text
/newbot
```

Keep the returned token private.

## 2. Find your chat ID

Set the token only in your local shell:

### PowerShell

```powershell
$env:TELEGRAM_BOT_TOKEN="YOUR_TOKEN"
python telegram_bot/get_chat_id.py
```

Before running the script, open your bot in Telegram, press **Start**, and send it a message.

The script prints your `chat_id`.

## 3. Test the local interactive bot

### PowerShell

```powershell
$env:TELEGRAM_BOT_TOKEN="YOUR_TOKEN"
$env:TELEGRAM_CHAT_ID="YOUR_CHAT_ID"
python telegram_bot/bot.py
```

Commands:

- `/today`
- `/report`
- `/wardrobe`
- `/help`

The local command bot only responds while this polling process is running.

## 4. Enable automatic GitHub Actions delivery

In GitHub repository settings, add Actions secrets:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Do not commit either value.

Set:

```yaml
delivery:
  channel: telegram
```

in `config/daily_assistant.yaml`.

The scheduled GitHub Action can then push the daily plan and learning report without your PC being online.
