# 🌙 Our Little Universe Bot

A Python-based Telegram bot for capturing personal memories, organizing story chapters, and revisiting meaningful moments through a simple command-driven interface, powered by SQLite.

## ✨ Features

- 💌 **Save Memories** — Store meaningful moments and personal memories.
- 📖 **Story Chapters** — Write and preserve chapters of your story.
- ⏳ **Memory Timeline** — Revisit saved memories and chapters in chronological order.
- 🦊 **Special Nicknames** — Display meaningful nicknames.
- 💬 **Interactive Commands** — Navigate the bot using Telegram commands.
- 💾 **SQLite Storage** — Save entries locally in a lightweight database.

## 🛠️ Tech Stack

- **Language:** Python
- **Bot Framework:** `python-telegram-bot`
- **Database:** SQLite
- **Version Control:** Git and GitHub

## 📋 Available Commands

| Command | Description |
|---|---|
| `/start` | Welcome to Our Little Universe |
| `/help` | Display available commands |
| `/memory` | Save a special memory |
| `/story` | Read saved memories and chapters |
| `/timeline` | Revisit saved moments |
| `/nicknames` | View special nicknames |
| `/chapter` | Write a new story chapter |
| `/cancel` | Cancel a pending memory or chapter |

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/betsiigit/ourLittleUniverseBot.git
cd ourLittleUniverseBot
```

### 2. Install Python

Install a compatible version of Python and verify your installation:

```bash
python --version
```

### 3. Install dependencies

```bash
python -m pip install python-telegram-bot
```

### 4. Configure your bot token

Create a Telegram bot using [@BotFather](https://t.me/BotFather) and obtain a fresh bot token.

Set the token as an environment variable in PowerShell:

```powershell
$env:TELEGRAM_BOT_TOKEN="YOUR_NEW_BOT_TOKEN"
```

Never commit your bot token to GitHub.

### 5. Run the bot

```bash
python main.py
```

Once the bot starts polling for updates, open your bot in Telegram and send `/start`.

## 💾 Data Storage

Memories and chapters are stored in a local SQLite database named `our_story.db`. The database is created automatically when the bot starts.

The database file is intended to remain local and should not be committed to the public repository.

## 🔐 Security

- Store bot credentials in environment variables.
- Keep tokens and `.env` files out of version control.
- Do not publish personal memories or private data in a public repository.
- Back up your local database securely if you want to preserve your entries.

## 🗺️ Future Improvements

- Add memory search and filtering.
- Support editing and deleting saved entries.
- Add dates and tags to memories.
- Improve privacy and access controls.
- Add automated tests and deployment documentation.

## 💗 Project Vision

Our Little Universe is a small digital space for meaningful moments, personal stories, and memories worth keeping.

*Our story, our memories, our little universe.* 🌌
