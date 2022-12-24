#!/usr/bin/env python3
"""
Listen to messages with tt and ii prefix
If a message begins with tt then it'll send a prompt to OpenAI Completion API
If a message begins with ii then it'll send a prompt to OpenAI Image API
"""
import logging
import os
from argparse import ArgumentParser, RawDescriptionHelpFormatter

import telegram
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, Updater

from common_utils import retry, setup_logging

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TEMPLATE")


def start(update: Update, _) -> None:
    keyboard = [
        [
            InlineKeyboardButton("Option 1", callback_data="1"),
            InlineKeyboardButton("Option 2", callback_data="2"),
        ],
        [InlineKeyboardButton("Option 3", callback_data="3")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text("Please choose:", reply_markup=reply_markup)


def button(update: Update, context: CallbackContext) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    query.answer()

    query.edit_message_text(text=f"Selected option: {query.data}")


def help_command(update: Update, _) -> None:
    update.message.reply_text("Help!")


@retry(telegram.error.TimedOut, tries=3)
def text_completion(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    logging.info(f"Text Completion Incoming update: {update} from {chat_id}")
    bot = context.bot
    bot.send_message(chat_id=chat_id, text="🤖 Text Completion")


@retry(telegram.error.TimedOut, tries=3)
def image_generation(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    logging.info(f"Image Generation Incoming update: {update} from {chat_id}")
    bot = context.bot
    bot.send_message(chat_id=chat_id, text="🖼️ Image Generation")


def main():
    """Start the bot."""
    logging.info("Starting open-ai bot")
    if not BOT_TOKEN:
        logging.error("🚫 Please make sure that you set the correct environment variable.")
        return False
    else:
        logging.info("🤖 Telegram bot token: %s", BOT_TOKEN[:5] + "..." + BOT_TOKEN[-5:])

    updater = Updater(BOT_TOKEN, use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("text", text_completion))
    dispatcher.add_handler(CommandHandler("image", image_generation))

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


if __name__ == "__main__":
    args = parse_args()
    setup_logging(args.verbose)
    main()
