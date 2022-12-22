import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

from common_utils import build_chart_links_for, setup_logging

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


def handle_cmd(update: Update, context: CallbackContext) -> None:
    print(f"Incoming update: {update}")
    maybe_symbol: str = update.message.text
    if maybe_symbol.startswith("$"):
        ticker = maybe_symbol[1:]
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


if __name__ == "__main__":
    setup_logging(2)
    main()
