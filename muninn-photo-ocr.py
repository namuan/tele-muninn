import logging
import os
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pathlib import Path
from typing import Dict, List

import telegram
from dotenv import load_dotenv
from py_executable_checklist.workflow import WorkflowBase, run_command

from common_utils import (
    retry,
    run_in_background,
    send_message_to_telegram,
    setup_logging,
    table_from,
)
from tele_bookmark_bot import PhotoOcr

# Common functions across steps
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")


class FetchNextAvailableBookmarkFromDatabase(WorkflowBase):
    """
    Fetch next bookmark with PhotoOcr source without a fileId
    """

    database_file_path: Path

    def execute(self) -> dict:
        with table_from(self.database_file_path) as db_table:
            logging.info("Selecting next batch of photos to convert to text from %s table", db_table.name)
            photos = db_table.find(source=PhotoOcr.__name__, remote_file_id=None)
            local_photos = {photo["id"]: Path(photo["content"]) for photo in photos}

        return {"local_photos": local_photos}


class ConvertImageToText(WorkflowBase):
    """
    Convert image to text using tesseract
    """

    local_photos: Dict[str, Path]
    database_file_path: Path

    def execute(self) -> dict:
        logging.info("Converting %s Photos", len(self.local_photos))
        converted_files = []
        for db_id, image_file_path in self.local_photos.items():
            image_name = image_file_path.stem
            text_path = image_file_path.parent / f"{image_name}"
            tesseract_command = f"tesseract {image_file_path} {text_path} --oem 1 -l eng"
            run_command(tesseract_command)
            text_path_with_suffix = text_path.with_suffix(".txt")
            logging.info(f"Updating database with local id {db_id} -> remote file id: {text_path_with_suffix}")
            with table_from(self.database_file_path) as db_table:
                db_table.update({"id": db_id, "remote_file_id": text_path_with_suffix.as_posix()}, ["id"])
            converted_files.append(text_path_with_suffix)
        return {"converted_files": converted_files}


class SendTextToTelegram(WorkflowBase):
    """
    Send converted text to telegram
    """

    converted_files: List[Path]

    def execute(self):
        logging.info("Sending OCR text for %s Photos", len(self.converted_files))
        for converted_text_file_path in self.converted_files:
            converted_text = converted_text_file_path.read_text()
            self.send_message_with_retries(converted_text)

    @retry(telegram.error.TimedOut, tries=3)
    def send_message_with_retries(self, converted_text):
        send_message_to_telegram(BOT_TOKEN, GROUP_CHAT_ID, converted_text, disable_web_preview=False)


def workflow():
    return [
        FetchNextAvailableBookmarkFromDatabase,
        ConvertImageToText,
        SendTextToTelegram,
    ]


def parse_args():
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("-d", "--database-file-path", type=Path, required=True, help="Path to database file")
    parser.add_argument(
        "-b", "--batch", action="store_true", default=False, help="Run in batch mode (no scheduling, just run once)"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        dest="verbose",
        help="Increase verbosity of logging output. Display context variables between each step run",
    )
    return parser.parse_args()


if __name__ == "__main__":
    print("Running Muninn-OCR")
    args = parse_args()
    setup_logging(args.verbose)
    context = args.__dict__
    run_in_background(context, workflow())
