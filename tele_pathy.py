#!/usr/bin/env python3
"""
Receive voice messages from Telegram and convert them to text using OpenAI Whisper
Then send the text to OpenAI GPT-3 to generate a response
Then convert the response back to audio using TTS
Then send the audio back to Telegram
"""
import logging
import os
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pathlib import Path

import telegram
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

import voice_to_openai
from common_utils import retry, setup_logging, uuid_gen, verified_chat_id

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TEMPLATE")
OUTPUT_DIR = Path.home().joinpath("OutputDir").joinpath("tele_pathy")


def start(update: Update, _) -> None:
    update.message.reply_text("👋 Send a voice message")


def help_command(update: Update, _) -> None:
    update.message.reply_text("Help!")


def save_voice_file(update: Update):
    voice_file = update.message.voice.get_file()
    file_path = OUTPUT_DIR / f"{uuid_gen()}.ogg"
    voice_file.download(file_path.as_posix())
    logging.info(f"Saved voice message to {file_path}")
    return file_path


@retry(telegram.error.TimedOut, tries=3)
def handle_voice_message(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    if not verified_chat_id(chat_id):
        return
    logging.info(f"Received voice message: {update} from {chat_id}")
    message_sent = context.bot.send_message(chat_id=chat_id, text="🎤 Processing voice message")
    file_path = save_voice_file(update)
    generated_output_file_path = voice_to_openai.run(file_path)
    logging.info(f"Sending audio response at {generated_output_file_path} to {chat_id}")
    context.bot.send_voice(chat_id=chat_id, voice=open(generated_output_file_path, "rb"))
    context.bot.delete_message(chat_id=chat_id, message_id=message_sent.message_id)


def main():
    """Start the bot."""
    logging.info("Starting Tele-Pathy bot")
    if not BOT_TOKEN:
        logging.error("🚫 Please make sure that you set the correct environment variable.")
        return False
    else:
        logging.info('🤖 Telegram bot token: "%s"', BOT_TOKEN[:5] + "..." + BOT_TOKEN[-5:])

    updater = Updater(BOT_TOKEN, use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(MessageHandler(Filters.voice & ~Filters.command, handle_voice_message))

    updater.start_polling()

    updater.idle()


def parse_args():
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=1,
        dest="verbose",
        help="Increase verbosity of logging output",
    )
    return parser.parse_args()


def setup_directories():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    setup_directories()
    args = parse_args()
    setup_logging(args.verbose)
    main()
