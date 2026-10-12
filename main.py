
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Final

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Read your new token from an environment variable.
TOKEN:Final= '8665822377:AAHkKN3QipqSwl6uP_BgK_fnvITGg4ilwII'

# Replace this with your actual Telegram bot username.
BOT_USERNAME: Final = "@OurLittleUniverseBot"

DB_PATH = Path(__file__).with_name("our_story.db")


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


def save_entry(kind: str, content: str):
    created_at = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO entries (kind, content, created_at)
            VALUES (?, ?, ?)
            """,
            (kind, content, created_at),
        )


def get_entries(kind=None):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        if kind:
            rows = conn.execute(
                """
                SELECT * FROM entries
                WHERE kind = ?
                ORDER BY id ASC
                """,
                (kind,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM entries ORDER BY id ASC"
            ).fetchall()

        return [dict(row) for row in rows]


async def start_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    context.user_data.pop("awaiting_entry", None)

    await update.effective_message.reply_text(
        "A little home for your memories and story.\n\n"
        "Use /memory to save a memory, /chapter to write "
        "a chapter, or /story to read your story.\n\n"
        "Type /help to see all commands. 💗"
    )


async def help_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    await update.effective_message.reply_text(
        "🌙 OUR LITTLE UNIVERSE — COMMANDS\n\n"
        "/story - Read our story\n"
        "/memory - Save a special memory\n"
        "/timeline - Revisit saved moments\n"
        "/nicknames - Our special nicknames\n"
        "/chapter - Save a new chapter\n"
        "/start - Welcome home\n"
        "/help - Show this menu\n\n"
        "You can also type /memory followed by your memory."
    )


async def custom_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    await update.effective_message.reply_text(
        "✨ A little universe, just one memory at a time."
    )


async def save_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    kind: str,
):
    message = update.effective_message
    content = " ".join(context.args).strip()

    if content:
        save_entry(kind, content)
        label = "memory" if kind == "memory" else "chapter"

        await message.reply_text(
            f"💗 Your {label} has been saved!\n\n"
            f"“{content}”"
        )
        return

    context.user_data["awaiting_entry"] = kind

    if kind == "memory":
        prompt = (
            "💌 What memory would you like to keep?\n\n"
            "Tell me what happened, and I'll save it."
        )
    else:
        prompt = (
            "📖 What is this new chapter about?\n\n"
            "Write your chapter in a message, and I'll save it."
        )

    await message.reply_text(
        prompt + "\n\nSend /cancel if you change your mind."
    )


async def memory_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    await save_command(update, context, "memory")


async def chapter_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    await save_command(update, context, "chapter")


async def cancel_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    context.user_data.pop("awaiting_entry", None)

    await update.effective_message.reply_text(
        "Okay 💗 Nothing new was saved."
    )


async def story_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    entries = get_entries()

    if not entries:
        await update.effective_message.reply_text(
            "📖 Our story is waiting for its first memory.\n\n"
            "Use /memory to begin your story. 💗"
        )
        return

    lines = ["🌙 OUR LITTLE UNIVERSE\n"]

    for entry in entries:
        label = (
            "📖 Chapter"
            if entry["kind"] == "chapter"
            else "💌 Memory"
        )
        lines.append(f"{label}\n{entry['content']}")

    text = "\n\n".join(lines)

    # Telegram messages have a length limit.
    for start in range(0, len(text), 3500):
        await update.effective_message.reply_text(
            text[start:start + 3500]
        )


async def timeline_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    entries = get_entries()

    if not entries:
        await update.effective_message.reply_text(
            "⏳ Your timeline is waiting for its first memory."
        )
        return

    lines = ["⏳ OUR TIMELINE\n"]

    for entry in entries:
        try:
            dt = datetime.fromisoformat(entry["created_at"])
            date_text = dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            date_text = entry["created_at"]

        label = (
            "Chapter"
            if entry["kind"] == "chapter"
            else "Memory"
        )

        lines.append(
            f"• {date_text} — {label}: {entry['content']}"
        )

    text = "\n".join(lines)

    for start in range(0, len(text), 3500):
        await update.effective_message.reply_text(
            text[start:start + 3500]
        )


async def nicknames_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    await update.effective_message.reply_text(
        "🐰 OUR SPECIAL NICKNAMES 🦊\n\n"
        "👑 Mprin — My princess\n"
        "💗 Flexie — Fluffle + my Flex \n"
        "🌙 Our Little Universe — The home of our story\n\n"
        "Add more nicknames to this list whenever you like."
    )


async def handle_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    message = update.effective_message

    if not message or not message.text:
        return

    text = message.text.strip()
    pending_kind = context.user_data.get("awaiting_entry")

    if pending_kind:
        if text.startswith("/"):
            await message.reply_text(
                "You can use /cancel to stop saving, "
                "or send your memory as ordinary text."
            )
            return

        save_entry(pending_kind, text)
        context.user_data.pop("awaiting_entry", None)

        label = (
            "chapter"
            if pending_kind == "chapter"
            else "memory"
        )

        await message.reply_text(
            f"💗 Your {label} has been saved safely!\n\n"
            f"“{text}”"
        )
        return

    chat_type = message.chat.type

    if chat_type in ("group", "supergroup"):
        if BOT_USERNAME.lower() not in text.lower():
            return

        text = text.replace(BOT_USERNAME, "").strip()

    processed = text.lower()

    if "hello" in processed:
        response = "Hey there! 🌙"
    elif "how are you" in processed:
        response = "I'm good! How about you? 💗"
    elif "i am good too" in processed:
        response = "Good to hear! 👉💗"
    else:
        response = (
            "I'm still learning! Try /help to explore "
            "Our Little Universe. 🌙"
        )

    await message.reply_text(response)


async def error_handler(
    update: object, context: ContextTypes.DEFAULT_TYPE
):
    print(f"An error occurred: {context.error}")


def main():
    if not TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is missing. Set your new "
            "bot token in the terminal before running."
        )

    init_db()

    print("Starting Our Little Universe...")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("custom", custom_command))
    app.add_handler(CommandHandler("memory", memory_command))
    app.add_handler(CommandHandler("chapter", chapter_command))
    app.add_handler(CommandHandler("story", story_command))
    app.add_handler(CommandHandler("timeline", timeline_command))
    app.add_handler(CommandHandler("nicknames", nicknames_command))
    app.add_handler(CommandHandler("cancel", cancel_command))

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    app.add_error_handler(error_handler)

    print("Polling for Telegram updates...")
    app.run_polling(poll_interval=3)


if __name__ == "__main__":
    main()
