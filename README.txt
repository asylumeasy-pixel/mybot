
Telegram Bot v2 — quick start (macOS)

This package includes:
- bot.py              : the Telegram bot (v2) with Google Sheets + PDF support
- requirements.txt    : python dependencies
- run_bot.command     : double-click to run the bot on macOS
- credentials.json    : NOT included. See below.
- users_v2.txt, progress_v2.json, ankety_v2.csv will be created after first run.

Important: Google Sheets integration requires a service account credentials file (credentials.json).
Steps to enable Google Sheets:
1) Go to Google Cloud Console -> Create a new project (or use existing).
2) Enable Google Sheets API and Google Drive API.
3) Create a Service Account -> Create Key -> JSON. Download and place it as 'credentials.json' into this folder.
4) Create a Google Sheet and note its name. Put that name into the GS_SPREADSHEET_NAME variable in bot.py if needed.
5) Share the Google Sheet with the service account email (found in credentials.json) with Editor access.
6) Restart the bot. It will append rows to the first sheet.

How to run:
1) Open Terminal and go to folder:
   cd /path/to/telegram_bot_v2
2) Install dependencies:
   pip3 install -r requirements.txt
3) Make run script executable (once):
   chmod +x run_bot.command
4) Double-click run_bot.command or run in terminal ./run_bot.command
5) Interact with bot in Telegram (/start).

Security note:
- The credentials.json contains sensitive keys. Do not share publicly.
- If your bot token was exposed, regenerate token in @BotFather.
