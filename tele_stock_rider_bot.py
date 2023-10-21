#!/usr/bin/env python3
"""
Listen to messages with a stock ticker starting with a $ sign and reply with a chart.
It also sends a messages with links to various websites with more information about the stock.
"""
import logging
import os
from argparse import ArgumentParser, RawDescriptionHelpFormatter

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

from common_utils import build_chart_links_for, retry, setup_logging, verified_chat_id

load_dotenv()

STOCK_RIDER_BOT_TOKEN = os.getenv("STOCK_RIDER_BOT_TOKEN")


def start(update: Update, _) -> None:
    update.message.reply_text("👋 Enter a stock ticker with a $ sign. Eg: $TSLA")


def help_command(update: Update, _) -> None:
    update.message.reply_text("Help!")


def generate_report(ticker, update: Update, context: CallbackContext):
    bot = context.bot
    cid = update.effective_chat.id
    update.message.reply_text(f"Looking up #{ticker}", quote=True)

    try:
        daily_chart_link, weekly_chart_link, full_message = build_chart_links_for(ticker)
        bot.send_photo(cid, daily_chart_link)
        bot.send_photo(cid, weekly_chart_link)
        bot.send_message(cid, full_message, disable_web_page_preview=True, parse_mode="Markdown")
    except NameError as e:
        bot.send_message(cid, str(e))


@retry(telegram.error.TimedOut, tries=3)
def handle_cmd(update: Update, context: CallbackContext) -> None:
    print(f"Incoming update: {update}")
    chat_id = update.effective_chat.id
    if not verified_chat_id(chat_id):
        return

    message_text: str = update.message.text
    if message_text.startswith("$"):
        ticker = message_text[1:]
        generate_report(ticker, update, context)


def main():
    """Start the bot."""
    logging.info("Starting tele-stock-rider bot")
    updater = Updater(STOCK_RIDER_BOT_TOKEN, use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_cmd))

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
