#!/usr/bin/env python3
"""
Telegram bot to download videos from social media websites
"""
import logging
import os
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pathlib import Path
from typing import Any

import telegram
import youtube_dl
from dotenv import load_dotenv
from py_executable_checklist.workflow import WorkflowBase, run_workflow
from telegram import Update
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from common_utils import retry, setup_logging, verified_chat_id

load_dotenv()

BOT_TOKEN = os.getenv("SOCIAL_VIDEO_BOT_TOKEN")

OUTPUT_DIR = Path.home().joinpath("OutputDir", "tele-bookmarks", "social-videos")


def welcome(update: Update, _):
    if update.message:
        update.message.reply_text(
            "👋 Hi there. ⬇️ I'm a bot to download social media videos ⬆️. " "Try sending me a link"
        )


def help_command(update: Update, _):
    if update.message:
        update.message.reply_text("Help!")


class AcknowledgeReceipt(WorkflowBase):
    """
    Acknowledge receipt of the message
    """

    input_url: str
    notifier: Any

    def execute(self) -> None:
        assert self.input_url is not None
        self.notifier.notify(f"Looking for video at {self.input_url}")


class DownloadMedia(WorkflowBase):
    """
    Download the media
    """

    input_url: str

    def execute(self) -> dict:
        ydl_opts = {
            "outtmpl": f"{OUTPUT_DIR}/%(title)s.%(ext)s",
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
            "socket_timeout": 10,
            "retries": 10,
            "prefer_ffmpeg": True,
            "keepvideo": False,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            media_info = ydl.extract_info(self.input_url, download=True)
            output_file = ydl.prepare_filename(media_info)
            logging.info(f"Downloaded {self.input_url} to {output_file}")

        return {"downloaded_media_file": output_file}


class CheckIfWithinSizeLimit(WorkflowBase):
    """
    Check if the media is within the telegram upload size limit
    """

    downloaded_media_file: str
    notifier: Any

    def execute(self):
        logging.info(f"Checking if {self.downloaded_media_file} is within size limit")
        file_size = Path(self.downloaded_media_file).stat().st_size
        if file_size > 50 * 1024 * 1024:
            self.notifier.notify("File too large to upload to telegram")


def workflow():
    return [
        AcknowledgeReceipt,
        DownloadMedia,
        CheckIfWithinSizeLimit,
    ]


def parse_args():
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("-i", "--input-url", help="Input url")
    parser.add_argument("-b", "--run-as-bot", action="store_true", default=False, help="Run as telegram bot")
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        dest="verbose",
        help="Increase verbosity of logging output. Display context variables between each step run",
    )
    return parser.parse_args()


class Notifier:
    def notify(self, message):
        print(message)


def main_workflow(context):
    context["notifier"] = Notifier()
    run_workflow(context, workflow())
    downloaded_media_file = context["downloaded_media_file"]
    logging.info(f"Downloaded '{downloaded_media_file}'")


@retry(telegram.error.TimedOut, tries=3)
def handle_video_url(update: Update, context):
    chat_id = update.effective_chat.id
    bot = context.bot
    original_message_id = update.message.message_id
    update_message_text = update.message.text

    logging.info(f"📡 Processing message: {update_message_text} from {chat_id}")

    if not verified_chat_id(chat_id):
        return

    context = {
        "input_url": update_message_text,
    }
    reply_message = bot.send_message(
        chat_id,
        "Got {}. 👀 at 📼".format(context["input_url"]),
        disable_web_page_preview=True,
    )
    main_workflow(context)
    downloaded_media_file = context["downloaded_media_file"]
    bot.edit_message_text(
        f"Uploading {downloaded_media_file} to telegram",
        chat_id,
        reply_message.message_id,
        disable_web_page_preview=True,
    )
    try:
        with open(downloaded_media_file, "rb") as video_file:
            bot.send_chat_action(chat_id, "upload_video")
            bot.send_video(
                chat_id,
                video_file,
                timeout=120,
            )
            bot.delete_message(chat_id, reply_message.message_id)
            bot.delete_message(chat_id, original_message_id)
    except telegram.error.NetworkError as e:
        logging.error(f"🚫 Network error: {e}")
        bot.edit_message_text(
            f"🚫 Network error: {e}",
            chat_id,
            reply_message.message_id,
            disable_web_page_preview=True,
        )


def main():
    """Start the bot."""
    logging.info("Starting tele-social-vdo bot")
    if not BOT_TOKEN:
        logging.error("🚫 Please make sure that you set the correct environment variable.")
        return False
    else:
        logging.info("🤖 Telegram bot token: %s", BOT_TOKEN[:5] + "..." + BOT_TOKEN[-5:])

    updater = Updater(BOT_TOKEN, use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", welcome))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_video_url))

    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    args = parse_args()
    setup_logging(args.verbose)
    if args.run_as_bot:
        main()
    else:
        context = args.__dict__
        main_workflow(context)
