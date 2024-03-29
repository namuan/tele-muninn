#!/usr/bin/env python3
"""
Bookmark notes, web pages, tweets, youtube videos, and photos.
"""
import argparse
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import dataset
import telegram
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from common_utils import retry, setup_logging, verified_chat_id
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

RIDER_BRAIN_BOT_TOKEN = os.getenv("RIDER_BRAIN_BOT_TOKEN")

OUTPUT_DIR = Path.home().joinpath("OutputDir", "tele-bookmarks", "web-to-pdf")

HOME_DIR = os.getenv("HOME")
DB_FILE = "rider_brain.db"
DB_CONNECTION_STRING = f"sqlite:///{HOME_DIR}/{DB_FILE}"
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


def update_user(bot, chat_id, original_message_id, reply_message_id, incoming_text):
    if "Photo" not in incoming_text:
        bot.delete_message(chat_id, original_message_id)
        bot.delete_message(chat_id, reply_message_id)
    bot.send_message(chat_id, f"🔖 {incoming_text} bookmarked")


class BaseHandler:
    def __init__(self, note):
        self.note: str = note

    def _find_existing_bookmark(self):
        return bookmarks_table.find_one(note=self.note)

    def bookmark(self) -> Optional[str]:
        existing_bookmark = self._find_existing_bookmark()
        if existing_bookmark:
            logging.info(f"Found one already bookmarked: {existing_bookmark}")
            return existing_bookmark["content"]

        archived_entry = self._bookmark()
        entry_row = {
            "source": self.__class__.__name__,
            "note": self.note,
            "created_at": datetime.now(),
            "content": archived_entry,
            "remote_file_id": None,
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
    def _bookmark(self) -> None:
        logging.info(f"Bookmarking WebPage: {self.note}")
        return None


class GitHub(WebPage):
    pass


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


class PhotoOcr(Photo):
    pass


class Document(BaseHandler):
    def __init__(self, note, document_file):
        super().__init__(note)
        self.document_file = document_file

    def _bookmark(self) -> str:
        target_file = OUTPUT_DIR / self.note
        self.document_file.download(target_file)
        logging.info(f"Document saved: {target_file}")
        return target_file.as_posix()


def message_handler_for(incoming_text) -> BaseHandler:
    if not incoming_text.startswith("http"):
        return PlainTextNote(incoming_text)

    incoming_url = incoming_text

    urls_to_handler = [
        {"urls": ["https://twitter.com"], "handler": Twitter},
        {"urls": ["https://youtube.com", "https://www.youtube.com", "https://m.youtube.com"], "handler": Youtube},
        {"urls": ["https://github.com", "https://www.github.com"], "handler": GitHub},
    ]

    for entry in urls_to_handler:
        for url in entry.get("urls"):
            logging.info(f"Checking {url} against {incoming_url}")
            if incoming_url.startswith(url):
                return entry.get("handler")(incoming_url)

    return WebPage(incoming_url)


def process_photo(update: Update) -> str:
    original_message_id = update.message.message_id
    update_message_text = update.message.text

    photo_file = update.message.photo[-1].get_file()

    photo_identifier = update_message_text or original_message_id
    update_message_caption = stripped_caption(update)
    if update_message_caption == "ocr":
        photo_handler = PhotoOcr(photo_identifier, photo_file)
    else:
        photo_handler = Photo(photo_identifier, photo_file)

    photo_handler.bookmark()

    return f"Photo {photo_identifier}"


def stripped_caption(update):
    if update.message.caption:
        return update.message.caption.strip().lower()
    else:
        return ""


def process_message(update: Update) -> None:
    update_message_text = update.message.text
    message_handler = message_handler_for(update_message_text)
    message_handler.bookmark()


def process_document(update) -> str:
    document_name = update.message.document.file_name
    document_file = update.message.document.get_file()
    document_handler = Document(document_name, document_file)
    document_handler.bookmark()
    return document_name


@retry(telegram.error.TimedOut, tries=3)
def adapter(update: Update, context):
    try:
        chat_id = update.effective_chat.id
        bot = context.bot
        original_message_id = update.message.message_id
        update_message_text = update.message.text

        logging.info(f"📡 Processing message: {update_message_text} from {chat_id}")

        if not verified_chat_id(chat_id):
            return

        reply_message = bot.send_message(
            chat_id,
            f"Got {update_message_text if update_message_text else 'it'}. 👀 at 🌎",
            disable_web_page_preview=True,
        )

        if update.message.photo:
            update_message_text = process_photo(update)
        elif update.message.document:
            update_message_text = process_document(update)
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


@retry(telegram.error.NetworkError, tries=3)
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
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=1,
        dest="verbose",
        help="Increase verbosity of logging output",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    setup_directories()
    setup_logging(args.verbose)
    start_bot()
