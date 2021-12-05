import logging
import os

from telegram import Update
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from tele_muninn.greetings import greet


def welcome(update: Update, _):
    """Handle start command"""
    if update.message:
        update.message.reply_text("Hi!")


def help_command(update: Update, _):
    """Handle help command"""
    if update.message:
        update.message.reply_text("Help!")


def handle_cmd(update: Update, _):
    """Handle all updates"""
    if update.message:
        logging.info(update.message.text)
        update.message.reply_text(greet())


def start_bot():
    """Start bot and hook callback functions"""
    print("🏗 Starting bot")
    bot_token = os.getenv("TELE_MUNINN_BOT_TOKEN")
    if not bot_token:
        print(
            "🚫 Bot token not found. Please make sure that you set the TELE_MUNINN_BOT_TOKEN environment variable."
        )
        return False

    updater = Updater(bot_token, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", welcome))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_cmd))

    updater.start_polling()
    updater.idle()
    return True
