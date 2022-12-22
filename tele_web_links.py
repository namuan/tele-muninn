#!/usr/bin/env python3
"""
Send links to telegram on a schedule
"""
import os
import time
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from datetime import datetime
from pathlib import Path

import schedule

from common_utils import send_message_to_telegram

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")


def send_link(website_url):
    if website_url.startswith("#"):
        return

    try:
        send_message_to_telegram(BOT_TOKEN, GROUP_CHAT_ID, website_url, disable_web_preview=False)
    except Exception as e:
        print(f"Error processing: {website_url} - {str(e)}")


def main():
    webpages = Path("webpages.txt").read_text().splitlines()
    for webpage in webpages:
        send_link(webpage)


def run():
    now = datetime.now()
    is_weekday = now.weekday() < 5
    selected_hr = 7
    before_open = now.time().hour == selected_hr
    print(f"Checking {now} - Hour: {now.time().hour} - Before Open - {before_open}")
    if is_weekday and before_open:
        print(f"{now} - Is Weekday: {is_weekday}, before_open: {before_open}")
        main()


def check_if_run():
    print(f"Running {datetime.now()}")
    schedule.every(1).hour.do(run)
    while True:
        schedule.run_pending()
        time.sleep(1 * 60 * 60)  # every 1/2 hour


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
    check_if_run()
    # main()
