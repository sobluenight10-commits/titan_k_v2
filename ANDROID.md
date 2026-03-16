# Olympus on Android 24/7

The unified Olympus system (Telegram alarms, blog new-post alerts, 06:45 Olympus / 07:00 blog) needs a **server that runs 24/7**. Your laptop was off, so no messages were sent. Use an **Android phone** (e.g. with Termux) as the always-on server.

## 1. Same .env on laptop and Android

Use **one** set of credentials everywhere:

- `TELEGRAM_BOT_TOKEN` — from [@BotFather](https://t.me/BotFather)
- `TELEGRAM_CHAT_ID` — your chat id (send `/start` to your bot, then message [@userinfobot](https://t.me/userinfobot) to get your id)

Config accepts `TELEGRAM_TOKEN` as alias for `TELEGRAM_BOT_TOKEN`. Phone scheduler and main app both read these.

## 2. Run on Android (Termux)

1. Install [Termux](https://termux.dev/), then Python and pip.
2. Copy the `titan_k_v2` folder to the phone (or clone).
3. Create `.env` in `titan_k_v2` with:
   - `TELEGRAM_BOT_TOKEN=...`
   - `TELEGRAM_CHAT_ID=...`
   - `OPENAI_API_KEY=...` (needed for Olympus + blog analysis)
4. Install deps: `pip install -r requirements.txt`
5. Run the **full system** (bot + scheduler + blog monitor):
   ```bash
   python run_android.py
   ```
6. Keep Termux in the background (or use [Termux:Boot](https://wiki.termux.com/wiki/Termux:Boot) to start on boot).

You will get:

- Reply to `/start`, `/olympus`, `/blog`, etc.
- **06:45** Berlin — Olympus dashboard update + Telegram summary
- **07:00** Berlin — Blog summary
- **New blog post** — Telegram alert within ~15 min

## 3. If you get no reply to /start

- **Bot not running** — Start the server (e.g. `python run_android.py` on Android or `python main.py` on laptop).
- **Wrong chat** — If you see “This chat is not configured”, the bot will show your chat ID. Put `TELEGRAM_CHAT_ID=<that id>` in `.env` and restart.
- **Wrong token** — Check `TELEGRAM_BOT_TOKEN` in `.env` (no quotes, no spaces).

## 4. Lightweight option (no Olympus, no GPT)

If you only want blog + stock alerts and 07:00 briefing **without** Olympus or GPT:

```bash
python phone_scheduler.py
```

Uses the same `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`. No OpenAI needed.

## 5. Olympus dashboard “old output”

The dashboard is the generated file `data/OLYMPUS_LIVE.html`. It is updated only when an Olympus run happens (06:45 scheduled or manual).

To refresh it now:

- **Windows:** Double‑click `Refresh Olympus.bat` or run:
  ```bash
  python refresh_olympus.py
  ```
- **With Telegram:** `python refresh_olympus.py --send`

Then open `data/OLYMPUS_LIVE.html` in a browser (or your deployed URL).
