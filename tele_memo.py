#!/usr/bin/env python3
"""
Spaced Repetition using Telegram Bot
"""
import argparse
import logging
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from random import choice

import telegram
from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

from common_utils import retry, setup_logging, verified_chat_id

load_dotenv()

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("A6QI320OG5_BOT_TOKEN")


# Define the command handler for the /start command
def start(update: Update, context: CallbackContext) -> None:
    reply_keyboard = [["Ask Next Question"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text("Press the button to ask the next question.", reply_markup=markup)


qa_data_filepath: str = None


def get_random_question_from_xml():
    assert qa_data_filepath is not None

    tree = ET.parse(qa_data_filepath)
    root = tree.getroot()
    cards = root.findall(".//card")
    card = choice(cards)
    question = card.find(".//text[@name='Front']").text
    answer = card.find(".//text[@name='Back']").text

    # Remove unusual new lines
    question = question.replace("\n", " ")
    answer = answer.replace("\n", " ")

    # Remove unusual new lines and excessive spaces
    question = re.sub(r"\s+", " ", question)
    answer = re.sub(r"\s+", " ", answer)

    return {"question": question.strip(), "answer": answer.strip()}


# Dictionary to store the current question for each user
user_data = {}


@retry(telegram.error.TimedOut, tries=3)
def button_handler(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text
    user_id = update.message.from_user.id
    if not verified_chat_id(user_id):
        return

    if user_input == "Ask Next Question":
        ask_next_question(update, user_id)
    elif user_input == "Flip":
        display_answer(update, user_id)
    elif user_input in ["🔴 Hard", "🟡 Fair", "🟢 Easy"]:
        logger.info(f"Button pressed: {user_input}")
        # Reset the user data after rating
        if user_id in user_data:
            del user_data[user_id]
        ask_next_question(update, user_id)


def display_answer(update, user_id):
    if user_id in user_data:
        answer = user_data[user_id]["answer"]
        logger.info("Button pressed: Flip")
        reply_keyboard = [["🔴 Hard", "🟡 Fair", "🟢 Easy"]]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text(f"{answer}", reply_markup=markup)
    else:
        ask_next_question(update, user_id)


def ask_next_question(update, user_id):
    qa_pair = get_random_question_from_xml()
    user_data[user_id] = qa_pair
    logger.info("Button pressed: Ask Next Question")
    reply_keyboard = [["Flip"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(f'<b>Question</b>\n{qa_pair["question"]}', parse_mode="HTML", reply_markup=markup)


def main(args) -> None:
    global qa_data_filepath
    qa_data_filepath = args.database
    updater = Updater(BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register the handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, button_handler))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()


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
    parser.add_argument("-i", "--database", type=Path, required=True, help="QA Database")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    setup_logging(args.verbose)
    main(args)
