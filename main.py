
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


# ==========================================
# CONFIGURATION
# ==========================================

TOKEN: Final = os.getenv("TELEGRAM_BOT_TOKEN")
BOT_USERNAME: Final = "@OurLittleUniverseBot"

OWNER_ID = int(os.getenv("TELEGRAM_OWNER_ID", "0"))
COOWNER_ID = int(os.getenv("TELEGRAM_COOWNER_ID", "0"))

DB_PATH = Path(__file__).with_name("our_story.db")


# ==========================================
# AUTHORIZATION
# ==========================================

def is_authorized(update: Update) -> bool:
    """Allow only the owner and approved co-owner."""

    user = update.effective_user

    return (
        user is not None
        and user.id in {OWNER_ID, COOWNER_ID}
        and user.id != 0
    )


async def deny_unauthorized(update: Update) -> bool:
    """Block users who are not authorized."""

    if not is_authorized(update):
        message = update.effective_message

        if message:
            await message.reply_text(
                "🔒 This little universe is private. 💗"
            )

        return True

    return False


# ==========================================
# DATABASE
# ==========================================

def init_db():
    """Create the database and safely add photo support."""

    with sqlite3.connect(DB_PATH) as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kind TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                photo_file_id TEXT
            )
        """)

        # Safely migrate existing databases.
        columns = {
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(entries)"
            )
        }

        if "photo_file_id" not in columns:
            conn.execute(
                "ALTER TABLE entries ADD COLUMN photo_file_id TEXT"
            )


def save_entry(
    kind: str,
    content: str,
    photo_file_id: str | None = None,
):
    """Save a memory or chapter, optionally with a photo."""

    created_at = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO entries (
                kind,
                content,
                created_at,
                photo_file_id
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                kind,
                content,
                created_at,
                photo_file_id,
            ),
        )


def get_entries(kind=None):
    """Retrieve saved memories and chapters."""

    with sqlite3.connect(DB_PATH) as conn:

        conn.row_factory = sqlite3.Row

        if kind:
            rows = conn.execute(
                """
                SELECT *
                FROM entries
                WHERE kind = ?
                ORDER BY id ASC
                """,
                (kind,),
            ).fetchall()

        else:
            rows = conn.execute(
                """
                SELECT *
                FROM entries
                ORDER BY id ASC
                """
            ).fetchall()

        return [dict(row) for row in rows]


# ==========================================
# DISPLAY SAVED MEMORIES
# ==========================================

async def send_saved_entry(message, entry):
    """Display a memory or chapter with its photo if available."""

    label = (
        "📖 Chapter"
        if entry["kind"] == "chapter"
        else "💌 Memory"
    )

    content = entry["content"]
    photo_file_id = entry.get("photo_file_id")

    if photo_file_id:

        caption = f"{label}\n\n{content}"

        if len(caption) <= 1024:

            await message.reply_photo(
                photo=photo_file_id,
                caption=caption,
            )

        else:

            await message.reply_photo(
                photo=photo_file_id,
                caption=label,
            )

            for start in range(0, len(content), 3500):
                await message.reply_text(
                    content[start:start + 3500]
                )

    else:

        response = f"{label}\n\n{content}"

        for start in range(0, len(response), 3500):
            await message.reply_text(
                response[start:start + 3500]
            )


# ==========================================
# START COMMAND
# ==========================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if await deny_unauthorized(update):
        return

    context.user_data.pop("awaiting_entry", None)
    context.user_data.pop("awaiting_photo", None)
    context.user_data.pop("pending_memory_content", None)

    await update.effective_message.reply_text(
        "🌙 Welcome to Our Little Universe 💗\n\n"
        "A little home for your memories and story.\n\n"
        "Use /memory to save a memory,\n"
        "/chapter to write a chapter,\n"
        "or /story to read your story.\n\n"
        "Type /help to see all commands. 🦊🐰"
    )


# ==========================================
# HELP COMMAND
# ==========================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if await deny_unauthorized(update):
        return

    await update.effective_message.reply_text(
        "🌙 OUR LITTLE UNIVERSE — COMMANDS\n\n"

        "📖 STORY\n"
        "/story - Read our story\n"
        "/timeline - Revisit saved moments\n"
        "/search keyword - Search our memories\n\n"

        "💌 SAVE MOMENTS\n"
        "/memory - Save a special memory\n"
        "/chapter - Save a new chapter\n"
        "/skip - Save a memory without a photo\n"
        "/cancel - Cancel the current save\n\n"

        "🐰 OUR LITTLE WORLD\n"
        "/nicknames - Our special nicknames\n"
        "/custom - A little universe message\n\n"

        "🌙 GENERAL\n"
        "/start - Welcome home\n"
        "/help - Show this menu\n\n"

        "You can also use /memory followed by your memory.\n"
        "Attach a photo to keep it with your memory. 💗"
    )


# ==========================================
# CUSTOM COMMAND
# ==========================================

async def custom_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if await deny_unauthorized(update):
        return

    await update.effective_message.reply_text(
        "✨ A little universe, just one memory at a time."
    )


# ==========================================
# SAVE COMMAND
# ==========================================

async def save_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    kind: str,
):
    if await deny_unauthorized(update):
        return

    message = update.effective_message

    if message is None:
        return

    # Clear an older pending save.
    context.user_data.pop("awaiting_entry", None)
    context.user_data.pop("awaiting_photo", None)
    context.user_data.pop("pending_memory_content", None)

    content = " ".join(context.args).strip()

    # Memory supplied directly with the command.
    if content:

        if kind == "memory":

            context.user_data["pending_memory_content"] = content
            context.user_data["awaiting_photo"] = True

            await message.reply_text(
                "💗 Your memory is ready!\n\n"
                "Now send a photo to keep with it,\n"
                "or send /skip to save it without a photo."
            )

        else:

            save_entry(kind, content)

            await message.reply_text(
                f"📖 Your chapter has been saved!\n\n"
                f"“{content}”"
            )

        return

    # Ask the user to provide text.
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


# ==========================================
# MEMORY COMMAND
# ==========================================

async def memory_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await save_command(update, context, "memory")


# ==========================================
# CHAPTER COMMAND
# ==========================================

async def chapter_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await save_command(update, context, "chapter")


# ==========================================
# CANCEL COMMAND
# ==========================================

async def cancel_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if await deny_unauthorized(update):
        return

    context.user_data.pop("awaiting_entry", None)
    context.user_data.pop("awaiting_photo", None)
    context.user_data.pop("pending_memory_content", None)

    await update.effective_message.reply_text(
        "Okay 💗 Nothing new was saved."
    )


# ==========================================
# SKIP PHOTO COMMAND
# ==========================================

async def skip_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if await deny_unauthorized(update):
        return

    message = update.effective_message

    content = context.user_data.get(
        "pending_memory_content"
    )

    if not content:

        await message.reply_text(
            "There isn't a memory waiting to be saved. 💗"
        )

        return

    save_entry("memory", content)

    context.user_data.pop("pending_memory_content", None)
    context.user_data.pop("awaiting_photo", None)

    await message.reply_text(
        "💗 Your memory has been saved without a photo!"
    )


# ==========================================
# PHOTO HANDLER
# ==========================================

async def photo_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if await deny_unauthorized(update):
        return

    message = update.effective_message

    if not message or not message.photo:
        return

    # Use the largest available Telegram photo.
    photo_file_id = message.photo[-1].file_id

    content = context.user_data.get(
        "pending_memory_content"
    )

    # Save the photo with a memory already being written.
    if context.user_data.get("awaiting_photo") and content:

        save_entry(
            "memory",
            content,
            photo_file_id,
        )

        context.user_data.pop("pending_memory_content", None)
        context.user_data.pop("awaiting_photo", None)

        await message.reply_text(
            "💗 Your memory and photo have been saved together!\n\n"
            "Use /story whenever you want to revisit this moment. 🌙"
        )

        return

    # Also support sending a photo with a caption.
    if message.caption and message.caption.strip():

        save_entry(
            "memory",
            message.caption.strip(),
            photo_file_id,
        )

        await message.reply_text(
            "💗 Your photo memory has been saved!"
        )

        return

    await message.reply_text(
        "🌙 To save a photo with a memory, first send /memory "
        "and tell me what happened."
    )


# ==========================================
# STORY COMMAND
# ==========================================

async def story_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if await deny_unauthorized(update):
        return

    message = update.effective_message

    entries = get_entries()

    if not entries:

        await message.reply_text(
            "📖 Our story is waiting for its first memory.\n\n"
            "Use /memory to begin your story. 💗"
        )

        return

    await message.reply_text(
        "🌙 OUR LITTLE UNIVERSE\n"
        "Every little moment matters. 💗"
    )

    for entry in entries:
        await send_saved_entry(message, entry)


# ==========================================
# TIMELINE COMMAND
# ==========================================

async def timeline_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if await deny_unauthorized(update):
        return

    message = update.effective_message

    entries = get_entries()

    if not entries:

        await message.reply_text(
            "⏳ Your timeline is waiting for its first memory."
        )

        return

    await message.reply_text(
        "⏳ OUR TIMELINE\n"
        "A collection of moments worth remembering. 💗"
    )

    for entry in entries:

        try:

            dt = datetime.fromisoformat(
                entry["created_at"]
            )

            date_text = dt.strftime("%Y-%m-%d %H:%M")

        except ValueError:

            date_text = entry["created_at"]

        await message.reply_text(
            f"📅 {date_text}"
        )

        await send_saved_entry(message, entry)


# ==========================================
# SEARCH COMMAND
# ==========================================

async def search_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if await deny_unauthorized(update):
        return

    message = update.effective_message

    if message is None:
        return

    query = " ".join(context.args).strip()

    if not query:

        await message.reply_text(
            "🔎 What memory are we looking for?\n\n"
            "Usage: /search keyword\n"
            "Example: /search princess"
        )

        return

    try:

        with sqlite3.connect(DB_PATH) as conn:

            conn.row_factory = sqlite3.Row

            rows = conn.execute(
                """
                SELECT
                    id,
                    kind,
                    content,
                    created_at,
                    photo_file_id
                FROM entries
                WHERE content LIKE ?
                ORDER BY id DESC
                LIMIT 10
                """,
                (f"%{query}%",),
            ).fetchall()

    except sqlite3.Error:

        await message.reply_text(
            "💫 I couldn't search our memories right now. "
            "Please try again later."
        )

        return

    if not rows:

        await message.reply_text(
            f"🌙 No memories found for: {query}"
        )

        return

    await message.reply_text(
        f"🔎 Memories matching: {query}"
    )

    for row in rows:
        await send_saved_entry(message, dict(row))


# ==========================================
# NICKNAMES COMMAND
# ==========================================

async def nicknames_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if await deny_unauthorized(update):
        return

    await update.effective_message.reply_text(
        "🐰 OUR SPECIAL NICKNAMES 🦊\n\n"
        "👑 Mprin — My princess\n"
        "💗 Flexie — Fluffle + my Flex\n"
        "🌙 Our Little Universe — The home of our story\n\n"
        "Add more nicknames to this list whenever you like."
    )


# ==========================================
# TEXT MESSAGE HANDLER
# ==========================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if await deny_unauthorized(update):
        return

    message = update.effective_message

    if not message or not message.text:
        return

    text = message.text.strip()

    pending_kind = context.user_data.get(
        "awaiting_entry"
    )

    # Waiting for a memory or chapter.
    if pending_kind:

        if text.startswith("/"):

            await message.reply_text(
                "You can use /cancel to stop saving, "
                "or send your memory as ordinary text."
            )

            return

        context.user_data.pop("awaiting_entry", None)

        if pending_kind == "memory":

            context.user_data["pending_memory_content"] = text
            context.user_data["awaiting_photo"] = True

            await message.reply_text(
                "💗 Beautiful. Your memory text is ready!\n\n"
                "Now send a photo to keep with it,\n"
                "or send /skip to save it without a photo."
            )

        else:

            save_entry("chapter", text)

            await message.reply_text(
                f"📖 Your chapter has been saved!\n\n"
                f"“{text}”"
            )

        return

    # Waiting for a photo.
    if context.user_data.get("awaiting_photo"):

        await message.reply_text(
            "📸 Send a photo for this memory,\n"
            "or use /skip to save it without a photo."
        )

        return

    # Group message behavior.
    chat_type = message.chat.type

    if chat_type in ("group", "supergroup"):

        if BOT_USERNAME.lower() not in text.lower():
            return

        text = text.replace(
            BOT_USERNAME,
            ""
        ).strip()

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


# ==========================================
# ERROR HANDLER
# ==========================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):
    print(f"An error occurred: {context.error}")


# ==========================================
# MAIN APPLICATION
# ==========================================

def main():

    if not TOKEN:

        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is missing. "
            "Set your new bot token in the terminal before running."
        )

    if OWNER_ID == 0 or COOWNER_ID == 0:

        raise RuntimeError(
            "TELEGRAM_OWNER_ID or TELEGRAM_COOWNER_ID is missing."
        )

    init_db()

    print("Starting Our Little Universe...")

    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("custom", custom_command))
    app.add_handler(CommandHandler("memory", memory_command))
    app.add_handler(CommandHandler("chapter", chapter_command))
    app.add_handler(CommandHandler("story", story_command))
    app.add_handler(CommandHandler("timeline", timeline_command))
    app.add_handler(CommandHandler("nicknames", nicknames_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CommandHandler("skip", skip_command))
    app.add_handler(CommandHandler("search", search_command))

    # Photos must have their own handler.
    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            photo_handler
        )
    )

    # Ordinary text messages.
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    app.add_error_handler(error_handler)

    print("Polling for Telegram updates...")

    app.run_polling(poll_interval=3)


if __name__ == "__main__":
    main()
