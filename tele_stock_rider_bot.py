#!/usr/bin/env python3
"""
Listen to messages with a stock ticker starting with a $ sign and reply with a chart.
It also sends a messages with links to various websites with more information about the stock.
"""
import asyncio
import io
import logging
import os
from argparse import ArgumentParser, RawDescriptionHelpFormatter

import requests
import telegram
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from common_utils import build_chart_links_for, retry, setup_logging, verified_chat_id

load_dotenv()

STOCK_RIDER_BOT_TOKEN = os.getenv("STOCK_RIDER_BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("👋 Enter a stock ticker with a $ sign. Eg: $TSLA")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Help!")


async def generate_report(ticker, update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    cid = update.effective_chat.id
    await update.message.reply_text(f"Looking up #{ticker}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        # Run blocking call in a thread
        daily_chart_link, weekly_chart_link, full_message = await asyncio.to_thread(build_chart_links_for, ticker)

        # Download images locally since Telegram can't fetch them from stockcharts.com
        logging.info(f"Downloading daily chart: {daily_chart_link}")
        daily_image = await asyncio.to_thread(
            lambda: requests.get(daily_chart_link, headers=headers, timeout=10).content
        )

        logging.info(f"Downloading weekly chart: {weekly_chart_link}")
        weekly_image = await asyncio.to_thread(
            lambda: requests.get(weekly_chart_link, headers=headers, timeout=10).content
        )

        # Send the chart images as file uploads
        await bot.send_photo(cid, photo=io.BytesIO(daily_image), caption="📊 Daily Chart")
        await bot.send_photo(cid, photo=io.BytesIO(weekly_image), caption="📊 Weekly Chart")
        await bot.send_message(cid, full_message, disable_web_page_preview=True, parse_mode="Markdown")
    except telegram.error.BadRequest as e:
        logging.error(f"BadRequest error: {e}")
        await bot.send_message(cid, f"Error fetching chart images: {str(e)}")
    except NameError as e:
        await bot.send_message(cid, str(e))
    except Exception as e:
        logging.error(f"Error generating report for {ticker}: {e}")
        await bot.send_message(cid, f"An error occurred while processing {ticker}")


@retry(telegram.error.TimedOut, tries=3)
async def handle_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"Incoming update: {update}")
    chat_id = update.effective_chat.id
    if not verified_chat_id(chat_id):
        return

    message_text: str = update.message.text
    if message_text.startswith("$"):
        ticker = message_text[1:]
        await generate_report(ticker, update, context)


def main():
    """Start the bot."""
    logging.info("Starting tele-stock-rider bot")

    # Build Application (v20+)
    application = Application.builder().token(STOCK_RIDER_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cmd))

    logging.info("Bot running...")
    application.run_polling()


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
