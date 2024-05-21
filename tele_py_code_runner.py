#!/usr/bin/env python3
"""
Telegram bot to run Python code
"""
import logging
import os
import re
import subprocess
import tempfile
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

from common_utils import retry, setup_logging, verified_chat_id

load_dotenv()

BOT_TOKEN = os.getenv("Q6Q6HJ632R_BOT_TOKEN")


class CodeExecutor:
    def __init__(self, code):
        self.code = code

    def parse_and_install_packages(self):
        # Regular expression to find pip install commands
        pip_commands = re.findall(r"#\s*pip\s*install\s*([a-zA-Z0-9\-_]+)", self.code)
        for package in pip_commands:
            print(f"Installing package: {package}")
            subprocess.run(["python3", "-m", "pip", "install", package], check=True)

    def execute_code(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w") as tmp_file:
            custom_print_code = """
import sys

def custom_print(*args, sep=' ', end='\\n', file=None):
    output = sep.join(map(str, args)) + end
    sys.stdout.write(output)
    sys.stdout.flush()

# Assign the custom print function to the built-in print
print = custom_print
"""
            tmp_file.write(custom_print_code + self.code)
            tmp_file_path = tmp_file.name

        python_cmd = ["python3", tmp_file_path, "2>&1"]
        print(f"🤖 Running command: {python_cmd}")
        with subprocess.Popen(
            python_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ) as proc:
            try:
                yield from iter(proc.stdout.readline, "")
            except Exception as e:
                print(e)
            finally:
                proc.stdout.close()

        # Clean up the temporary file
        os.remove(tmp_file_path)

    def run(self):
        self.parse_and_install_packages()
        return self.execute_code()


def parse_args():
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
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


def start(update: Update, _) -> None:
    update.message.reply_text("👋 Enter code snippet to run")


def help_command(update: Update, _) -> None:
    update.message.reply_text("Help!")


@retry(telegram.error.TimedOut, tries=3)
def handle_cmd(update: Update, context: CallbackContext) -> None:
    print(f"Incoming update: {update}")
    chat_id = update.effective_chat.id
    if not verified_chat_id(chat_id):
        return

    message_text: str = update.message.text
    executor = CodeExecutor(message_text)
    bot = context.bot
    cid = update.effective_chat.id
    update.message.reply_text("⚡ Running code", quote=True)

    try:
        for output in executor.run():
            print(output, end="")
            bot.send_message(cid, output, disable_web_page_preview=True)
    except NameError as e:
        bot.send_message(cid, str(e))


def main():
    """Start the bot."""
    logging.info("Starting bot")
    updater = Updater(BOT_TOKEN, use_context=True)

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_cmd))

    updater.start_polling()

    updater.idle()


if __name__ == "__main__":
    args = parse_args()
    setup_logging(args.verbose)
    if args.run_as_bot:
        main()
    else:
        test_code = """
# pip install requests
import time
print("Starting...")
for i in range(3):
    print(f"Sleeping {i+1}")
    time.sleep(1)
print("Finished sleeping.")
    """
        executor = CodeExecutor(test_code)
        for output in executor.run():
            print(output, end="")
