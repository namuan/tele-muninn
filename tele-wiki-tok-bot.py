#!/usr/bin/env -S uv run --quiet --script
# /// script
# dependencies = [
#   "python-telegram-bot>=20.0",
#   "requests",
#   "python-dotenv",
# ]
# ///
"""
Wikipedia TikTok-style Telegram bot (simple)

Usage:
./wiki_tok_bot.py --database-file-path bot.db -v
"""

import argparse
import asyncio
import logging
import os
import sqlite3
import threading
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)


# -------------------------
# Logging (from template)
# -------------------------
def setup_logging(verbosity: int):
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Wikipedia TikTok-style Telegram bot")
    parser.add_argument(
        "-d",
        "--database-file-path",
        type=Path,
        default=Path("bot.db"),
        help="Path to SQLite database file",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v, -vv)",
    )
    return parser.parse_args()


# -------------------------
# Globals (simple by design)
# -------------------------
AI_MIN_INTERVAL = 3.0  # seconds between OpenRouter calls
AI_LAST_CALL = 0.0

WIKI_RETRIES = 3
AI_RETRIES = 3

PRELOAD_TARGET = 20  # how many ready articles to keep
PRELOAD_SLEEP = 5  # seconds between preload attempts


# -------------------------
# Wikipedia
# -------------------------
def fetch_wikipedia():
    for attempt in range(WIKI_RETRIES):
        try:
            r = requests.get(
                "https://en.wikipedia.org/api/rest_v1/page/random/summary",
                headers={"User-Agent": "WikiTokBot/1.0 (https://github.com/namuan/tele-muninn; educational bot)"},
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()

            image = None
            if "originalimage" in data:
                image = data["originalimage"]["source"]

            return {
                "title": data["title"],
                "extract": data["extract"][:800],
                "url": data["content_urls"]["desktop"]["page"],
                "image": image,
            }
        except Exception as e:
            logging.warning(f"Wikipedia fetch failed ({attempt + 1}): {e}")
            time.sleep(1)

    raise RuntimeError("Wikipedia fetch failed after retries")


# -------------------------
# OpenRouter AI rewrite
# -------------------------
def rewrite_with_ai(title, text, api_key, model):
    global AI_LAST_CALL

    # Rate limiting
    wait = AI_MIN_INTERVAL - (time.time() - AI_LAST_CALL)
    if wait > 0:
        time.sleep(wait)

    prompt = f"""
Rewrite the following Wikipedia content into a short, engaging, neutral fact.
Keep it under 80 words.
No emojis.
No hashtags.

Title: {title}

Content:
{text}
"""

    for attempt in range(AI_RETRIES):
        try:
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                },
                timeout=20,
            )
            r.raise_for_status()
            AI_LAST_CALL = time.time()
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logging.warning(f"AI rewrite failed ({attempt + 1}): {e}")
            time.sleep(2)

    raise RuntimeError("AI rewrite failed after retries")


# -------------------------
# Database
# -------------------------
def init_db(conn):
    cur = conn.cursor()
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS articles (
        title TEXT PRIMARY KEY,
        rewritten TEXT,
        url TEXT,
        image TEXT
    )
    """
    )
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS seen (
        user_id INTEGER,
        title TEXT,
        PRIMARY KEY (user_id, title)
    )
    """
    )
    conn.commit()


def cached_article_count(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM articles")
    return cur.fetchone()[0]


def get_article(conn, user_id, api_key, model):
    cur = conn.cursor()

    # 1. Try cached unseen article first
    cur.execute(
        """
        SELECT a.title, a.rewritten, a.url, a.image
        FROM articles a
        LEFT JOIN seen s
        ON a.title = s.title AND s.user_id = ?
        WHERE s.title IS NULL
        LIMIT 1
    """,
        (user_id,),
    )

    row = cur.fetchone()
    if row:
        title, rewritten, url, image = row
        cur.execute("INSERT INTO seen VALUES (?, ?)", (user_id, title))
        conn.commit()
        return title, rewritten, url, image

    # 2. Fallback: fetch live (same as before)
    for _ in range(5):
        wiki = fetch_wikipedia()
        title = wiki["title"]

        rewritten = rewrite_with_ai(title, wiki["extract"], api_key, model)
        cur.execute(
            "INSERT OR IGNORE INTO articles VALUES (?, ?, ?, ?)",
            (title, rewritten, wiki["url"], wiki["image"]),
        )
        conn.commit()

        cur.execute("INSERT OR IGNORE INTO seen VALUES (?, ?)", (user_id, title))
        conn.commit()
        return title, rewritten, wiki["url"], wiki["image"]

    raise RuntimeError("Failed to get article")


# -------------------------
# Background preload worker
# -------------------------
def preload_worker(conn, api_key, model):
    logging.info("Preload worker started")

    while True:
        try:
            count = cached_article_count(conn)

            if count >= PRELOAD_TARGET:
                time.sleep(PRELOAD_SLEEP)
                continue

            logging.debug(f"Preloading article ({count}/{PRELOAD_TARGET})")

            wiki = fetch_wikipedia()
            title = wiki["title"]

            cur = conn.cursor()
            cur.execute("SELECT 1 FROM articles WHERE title=?", (title,))
            if cur.fetchone():
                continue

            rewritten = rewrite_with_ai(
                wiki["title"],
                wiki["extract"],
                api_key,
                model,
            )

            cur.execute(
                "INSERT OR IGNORE INTO articles VALUES (?, ?, ?, ?)",
                (
                    wiki["title"],
                    rewritten,
                    wiki["url"],
                    wiki["image"],
                ),
            )
            conn.commit()

            time.sleep(1)

        except Exception as e:
            logging.warning(f"Preload worker error: {e}")
            time.sleep(5)


# -------------------------
# UI helpers
# -------------------------
def caption(title, rewritten):
    return f"*{title}*\n\n" f"{rewritten}\n\n" f"_Source: Wikipedia (CC BY-SA)_"


def keyboard(url):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("➡️ Next", callback_data="next"),
                InlineKeyboardButton("📖 Read more", url=url),
            ]
        ]
    )


# -------------------------
# Telegram handlers
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = context.bot_data["db"]
    api_key = context.bot_data["openrouter_key"]
    model = context.bot_data["openrouter_model"]

    # Run blocking DB/Network call in a thread
    title, rewritten, url, image = await asyncio.to_thread(get_article, conn, update.effective_user.id, api_key, model)

    if image:
        await update.message.reply_photo(
            photo=image,
            caption=caption(title, rewritten),
            reply_markup=keyboard(url),
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            caption(title, rewritten),
            reply_markup=keyboard(url),
            parse_mode="Markdown",
        )


async def next_article(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    conn = context.bot_data["db"]
    api_key = context.bot_data["openrouter_key"]
    model = context.bot_data["openrouter_model"]

    # Run blocking DB/Network call in a thread
    title, rewritten, url, image = await asyncio.to_thread(get_article, conn, q.from_user.id, api_key, model)

    if image:
        media = InputMediaPhoto(
            media=image,
            caption=caption(title, rewritten),
            parse_mode="Markdown",
        )
        await q.edit_message_media(
            media=media,
            reply_markup=keyboard(url),
        )
    else:
        await q.edit_message_text(
            caption(title, rewritten),
            reply_markup=keyboard(url),
            parse_mode="Markdown",
        )


# -------------------------
# Main
# -------------------------
def main(args):
    load_dotenv()

    bot_token = os.getenv("8I7QEEP0XIPJ_BOT_TOKEN")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    openrouter_model = os.getenv("OPENROUTER_PRIMARY_MODEL", "mistralai/mistral-7b-instruct")

    if not bot_token or not openrouter_key:
        raise RuntimeError("BOT_TOKEN or OPENROUTER_API_KEY missing")

    logging.info(f"Using database: {args.database_file_path}")

    conn = sqlite3.connect(str(args.database_file_path), check_same_thread=False)
    init_db(conn)

    # Build Application (v20+)
    application = Application.builder().token(bot_token).build()

    application.bot_data["db"] = conn
    application.bot_data["openrouter_key"] = openrouter_key
    application.bot_data["openrouter_model"] = openrouter_model

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(next_article))

    preloader = threading.Thread(
        target=preload_worker,
        args=(conn, openrouter_key, openrouter_model),
        daemon=True,
    )
    preloader.start()

    logging.info("Bot running...")
    application.run_polling()


if __name__ == "__main__":
    args = parse_args()
    setup_logging(args.verbose)
    main(args)
