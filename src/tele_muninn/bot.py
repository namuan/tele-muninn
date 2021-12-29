import os

from telegram import Update
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from tele_muninn.message_processor import IncomingMessage, handle_cmd


def welcome(update: Update, _):
    if update.message:
        update.message.reply_text("Hi!")


def help_command(update: Update, _):
    if update.message:
        update.message.reply_text("Help!")


def adapter(update: Update, _):
    in_message = IncomingMessage(text=update.message.text)
    response = handle_cmd(in_message)
    update.message.reply_text(response)


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
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, adapter))

    updater.start_polling()
    updater.idle()
    return True
