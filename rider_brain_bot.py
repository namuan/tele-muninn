#!/usr/bin/env python3
"""
🧠 Telegram bot to bookmark stuff
"""
import argparse
import logging
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import dataset
import openai
import telegram
from dotenv import load_dotenv
from slug import slug
from telegram import Update
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from common_utils import fetch_html_page, html_parser_from, retry, run_command
from twitter_api import get_tweet
from yt_api import video_title

load_dotenv()

logging.basicConfig(
    handlers=[logging.StreamHandler()],
    format="%(asctime)s - %(filename)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logging.captureWarnings(capture=True)

DEFAULT_BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

HOME_DIR = os.getenv("HOME")
DB_FILE = "rider_brain.db"
DB_CONNECTION_STRING = f"sqlite:///{HOME_DIR}/{DB_FILE}"
OUTPUT_DIR = Path.home().joinpath("OutputDir", "web-to-pdf")
BOOKMARKS_TABLE = "bookmarks"

db = dataset.connect(DB_CONNECTION_STRING)
logging.info(f"Connecting to database {DB_CONNECTION_STRING}")
logging.info(f"Creating table {BOOKMARKS_TABLE}")
bookmarks_table = db.create_table(BOOKMARKS_TABLE)


def welcome(update: Update, _):
    if update.message:
        update.message.reply_text("👋 Hi there. ⬇️ I'm a bot to save bookmarks ⬆️. " "Try sending me something")


def help_command(update: Update, _):
    if update.message:
        update.message.reply_text("Help!")


def handle_web_page(web_page_url: str) -> str:
    page_html = fetch_html_page(web_page_url)
    bs = html_parser_from(page_html)
    web_page_title = slug(bs.title.string if bs.title and bs.title.string else web_page_url)
    target_file = OUTPUT_DIR / f"{web_page_title}.pdf"
    cmd = f'./webpage_to_pdf.py -i "{web_page_url}" -o "{target_file}" --headless'
    run_command(cmd)
    return target_file.as_posix()


def update_user(bot, chat_id, original_message_id, reply_message_id, incoming_text):
    bot.delete_message(chat_id, original_message_id)
    bot.delete_message(chat_id, reply_message_id)
    bot.send_message(chat_id, f"🔖 {incoming_text} bookmarked")


def verified_chat_id(chat_id):
    auth_chat_id = os.getenv("AUTH_CHAT_ID")
    if chat_id != int(auth_chat_id):
        logging.warning(f"🚫 Chat ID {chat_id} is not authorized. Authorized Chat Id: {auth_chat_id}")
        return False
    return True


class BaseHandler:
    def __init__(self, note):
        self.note: str = note

    def _find_existing_bookmark(self):
        return bookmarks_table.find_one(note=self.note)

    def bookmark(self) -> str:
        existing_bookmark = self._find_existing_bookmark()
        if existing_bookmark:
            logging.info(f"Found one already bookmarked: {existing_bookmark}")
            return existing_bookmark.get("content")

        archived_entry = self._bookmark()
        entry_row = {
            "source": self.__class__.__name__,
            "note": self.note,
            "created_at": datetime.now(),
            "content": archived_entry,
        }
        bookmarks_table.insert(entry_row)
        logging.info(f"Updated database: {entry_row}")
        return archived_entry

    def _bookmark(self) -> str:
        pass


class Youtube(BaseHandler):
    def _bookmark(self) -> str:
        return video_title(self.note)


class Twitter(BaseHandler):
    def _bookmark(self) -> str:
        parsed_tweet = urlparse(self.note)
        tweet_id = os.path.basename(parsed_tweet.path)
        tweet = get_tweet(tweet_id)
        return tweet.text


class WebPage(BaseHandler):
    def _bookmark(self) -> str:
        logging.info(f"Bookmarking WebPage: {self.note}")
        return handle_web_page(self.note)


class PlainTextNote(BaseHandler):
    def _bookmark(self) -> str:
        return self.note


class Photo(BaseHandler):
    def __init__(self, note, photo_file):
        super().__init__(note)
        self.photo_file = photo_file

    def _bookmark(self) -> str:
        target_file = OUTPUT_DIR / f"{self.note}.png"
        self.photo_file.download(target_file)
        logging.info(f"Photo saved: {target_file}")
        return target_file.as_posix()


class OpenAiCompletion(BaseHandler):
    openai_completion_api_path: str = "https://api.openai.com/v1/engines/davinci/completions"

    def bookmark(self):
        completion = openai.Completion.create(engine="ada", prompt="Hello world")
        if completion.choices:
            return completion.choices[0].text
        return "No completion found"


class OpenAiDalle(BaseHandler):
    openai_dalle_api_path: str = "https://api.openai.com/v1/engines/davinci-codex/completions"

    def bookmark(self):
        return self.note


plain_text_handler_mapping = {
    "tt": OpenAiCompletion,
    "ii": OpenAiDalle,
}


def find_plain_text_handler(incoming_text):
    for prefix, handler in plain_text_handler_mapping.items():
        if incoming_text.startswith(prefix):
            return handler(incoming_text[len(prefix) :].strip())

    return None


def message_handler_for(incoming_text) -> BaseHandler:
    if not incoming_text.startswith("http"):
        plain_text_handler = find_plain_text_handler(incoming_text)
        if not plain_text_handler:
            return PlainTextNote(incoming_text)

        return plain_text_handler

    incoming_url = incoming_text

    urls_to_handler = [
        {"urls": ["https://twitter.com"], "handler": Twitter},
        {"urls": ["https://youtube.com", "https://www.youtube.com", "https://m.youtube.com"], "handler": Youtube},
    ]

    for entry in urls_to_handler:
        for url in entry.get("urls"):
            logging.info(f"Checking {url} against {incoming_url}")
            if incoming_url.startswith(url):
                return entry.get("handler")(incoming_url)

    return WebPage(incoming_url)


def process_photo(update: Update) -> None:
    original_message_id = update.message.message_id
    update_message_text = update.message.text

    photo_file = update.message.photo[-1].get_file()
    photo_handler = Photo(update_message_text or original_message_id, photo_file)
    photo_handler.bookmark()


def process_message(update: Update) -> None:
    update_message_text = update.message.text
    message_handler = message_handler_for(update_message_text)
    message_handler.bookmark()


@retry(telegram.error.TimedOut, tries=3)
def adapter(update: Update, context):
    try:
        chat_id = update.effective_chat.id
        if not verified_chat_id(chat_id):
            return

        bot = context.bot
        original_message_id = update.message.message_id
        update_message_text = update.message.text

        logging.info(f"📡 Processing message: {update_message_text} from {chat_id}")
        reply_message = bot.send_message(
            chat_id,
            f"Got {update_message_text}. 👀 at 🌎",
            disable_web_page_preview=True,
        )

        if update.message.photo:
            process_photo(update)
        else:
            process_message(update)

        update_user(bot, chat_id, original_message_id, reply_message.message_id, update_message_text)
        logging.info(f"✅ Document sent back to user {chat_id}")
    except telegram.error.TimedOut:
        raise
    except Exception as e:
        error_message = f"🚨 🚨 🚨 {e}"
        update.message.reply_text(error_message)
        raise e


def start_bot():
    """Start bot and hook callback functions"""
    logging.info("🏗 Starting bot")
    bot_token = os.getenv("RIDER_BRAIN_BOT_TOKEN")
    if not bot_token:
        logging.warning("🚫 Please make sure that you set the RIDER_BRAIN_BOT_TOKEN environment variable.")
        return False

    updater = Updater(bot_token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", welcome))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(MessageHandler(~Filters.command, adapter))

    updater.start_polling()
    updater.idle()
    return True


def setup_directories():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    setup_directories()
    start_bot()