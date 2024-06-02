#!/usr/bin/env python3
"""
Spaced Repetition using Telegram Bot
"""
import argparse
import logging
import os
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from pathlib import Path

import dataset
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

HOME_DIR = os.getenv("HOME")
DB_FILE = "tele_memo.db"
DB_CONNECTION_STRING = f"sqlite:///{HOME_DIR}/{DB_FILE}"
QA_SESSIONS_TABLE = "qa_sessions"

db = dataset.connect(DB_CONNECTION_STRING)
logger.info(f"Connecting to database {DB_CONNECTION_STRING}")
logger.info(f"Creating table {QA_SESSIONS_TABLE}")
qa_sessions_table = db.create_table(QA_SESSIONS_TABLE)


# Define the command handler for the /start command
def start(update: Update, context: CallbackContext) -> None:
    reply_keyboard = [["Ask Next Question"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text("Press the button to ask the next question.", reply_markup=markup)


def fetch_unasked_question():
    result = next(
        db.query(
            """
        SELECT question, answer
        FROM qa_sessions
        WHERE user_response IS NULL
        ORDER BY RANDOM()
        LIMIT 1
    """
        ),
        None,
    )
    return (result["question"], result["answer"]) if result else (None, None)


def fetch_question_for_review():
    today = date.today()
    result = next(
        db.query(
            """
        SELECT question, answer
        FROM qa_sessions
        WHERE next_review <= ?
        ORDER BY RANDOM()
        LIMIT 1
    """,
            (today,),
        ),
        None,
    )
    return (result["question"], result["answer"]) if result else (None, None)


def get_question_answer():
    # Step 2: Fetch Unasked Questions
    question, answer = fetch_unasked_question()

    # Step 3: Check if there are unasked questions
    if question:
        return {"question": question, "answer": answer}
    else:
        # Step 7: Fetch Questions for Regular Review
        question, answer = fetch_question_for_review()
        if question:
            return {"question": question, "answer": answer}
        else:
            return None  # No questions available for review


def calculate_next_review(user_response):
    today = date.today()
    if user_response == "🟢 Easy":
        return today + timedelta(days=4)
    elif user_response == "🟡 Fair":
        return today + timedelta(days=2)
    elif user_response == "🔴 Hard":
        return today + timedelta(days=1)
    else:
        raise ValueError("Invalid feedback value")


def store_qa_result(user_id, question, user_response):
    global qa_sessions_table
    # Create a dictionary for the entry
    entry_row = {
        "user_id": user_id,
        "question": question,
        "user_response": user_response,
        "updated_at": datetime.now(),
        "next_review": calculate_next_review(user_response),
    }

    qa_sessions_table.update(entry_row, ["question"])

    # Log the action
    logger.info(f"Stored QA result: {entry_row}")


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
        if user_id in user_data:
            qa_pair = user_data[user_id]
            store_qa_result(user_id, qa_pair["question"], user_input)
            # Reset the user data after rating
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
    qa_pair = get_question_answer()
    user_data[user_id] = qa_pair
    logger.info("Button pressed: Ask Next Question")
    reply_keyboard = [["Flip"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(f'<b>Question</b>\n{qa_pair["question"]}', parse_mode="HTML", reply_markup=markup)


def main(args) -> None:
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
    parser.add_argument(
        "-i",
        "--import-anki",
        action="store_true",
        default=False,
        help="Import Question Answers from Anki Exported XML file",
    )
    parser.add_argument("-s", "--source", type=Path, help="QA Database")
    return parser.parse_args()


def import_from_source(source: Path):
    tree = ET.parse(source)
    root = tree.getroot()
    cards = root.findall(".//card")
    for card in cards:
        question = card.find(".//text[@name='Front']").text
        answer = card.find(".//text[@name='Back']").text
        # Remove unusual new lines
        question = question.replace("\n", " ")
        answer = answer.replace("\n", " ")

        # Remove unusual new lines and excessive spaces
        question = re.sub(r"\s+", " ", question)
        answer = re.sub(r"\s+", " ", answer)

        # Create a dictionary for the entry
        entry_row = {
            "question": question.strip(),
            "answer": answer.strip(),
            "created_at": datetime.now(),
            "user_response": None,
        }
        # Insert the entry into the table
        qa_sessions_table.insert(entry_row)


if __name__ == "__main__":
    args = parse_args()
    setup_logging(args.verbose)
    if args.import_anki:
        import_from_source(args.source)
    else:
        main(args)
