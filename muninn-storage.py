#!/usr/bin/env python3
"""
Copy local files to GDrive remote storage
"""
import functools
import logging
import os
import time
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import dataset
import schedule
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from py_executable_checklist.workflow import WorkflowBase, run_workflow

from common_utils import setup_logging

load_dotenv()

GDRIVE_REMOTE_FOLDER_ID = os.getenv("GDRIVE_REMOTE_FOLDER_ID")

SCOPES = [
    "https://www.googleapis.com/auth/drive",
]

logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)


@contextmanager
def table_from(database_file_path: Path):
    db_connection_string = f"sqlite:///{database_file_path.as_posix()}"
    db = dataset.connect(db_connection_string)
    bookmarks_table = db.create_table("bookmarks")
    yield bookmarks_table
    db.close()


class ReadTokenFromFile(WorkflowBase):
    """
    Read the token from json file
    """

    token_file: Path

    def execute(self) -> dict:
        logging.info("Reading token from %s", self.token_file)
        credentials = Credentials.from_authorized_user_file(self.token_file.as_posix(), SCOPES)
        return {"credentials": credentials}


class RefreshTokenIfExpired(WorkflowBase):
    """
    Refresh the token if it is expired
    """

    credentials: Credentials

    def execute(self) -> dict:
        if self.credentials and self.credentials.expired and self.credentials.refresh_token:
            logging.info("Refreshing token as it is expired")
            self.credentials.refresh(Request())

        google_service = build("drive", "v3", credentials=self.credentials)
        return {"google_service": google_service}


class SelectPendingBookmarksToUpload(WorkflowBase):
    """
    Select next batch of files to upload from database
    """

    database_file_path: Path

    def execute(self) -> dict:
        with table_from(self.database_file_path) as db_table:
            logging.info("Selecting next batch of files to upload from %s table", db_table.name)
            web_pages = db_table.find(source="WebPage", content={"!=": "Not downloaded"}, remote_file_id=None)
            local_archived_files = {web_page["id"]: Path(web_page["content"]) for web_page in web_pages}

        return {"local_files": local_archived_files}


class UploadWebPagesToGDrive(WorkflowBase):
    """
    Upload selected web pages to GDrive
    """

    google_service: Any
    local_files: Dict[str, Path]
    database_file_path: Path

    def execute(self):
        logging.info("Uploading %s web pages to GDrive", len(self.local_files))
        for db_id, local_file in self.local_files.items():
            logging.info("Uploading %s to GDrive", local_file)
            file_metadata = {"name": local_file.stem, "parents": [GDRIVE_REMOTE_FOLDER_ID]}
            try:
                media = MediaFileUpload(local_file.as_posix(), mimetype="application/pdf")
                file = self.google_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
                uploaded_file_id = file.get("id")
                print(f"Updating database with local id {db_id} -> remote file id: {uploaded_file_id}")
                with table_from(self.database_file_path) as db_table:
                    db_table.update({"id": db_id, "remote_file_id": uploaded_file_id}, ["id"])
            except FileNotFoundError as e:
                logging.error("File Id: %s -> File not found: %s", db_id, local_file)
                raise e


def workflow():
    return [
        ReadTokenFromFile,
        RefreshTokenIfExpired,
        SelectPendingBookmarksToUpload,
        UploadWebPagesToGDrive,
    ]


def parse_args():
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("-d", "--database-file-path", type=Path, required=True, help="Path to database file")
    parser.add_argument(
        "-t", "--token-file", type=Path, required=True, help="Token file for authenticated GDrive access"
    )
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


def run_on_schedule(context):
    run_workflow(context, workflow())


def main(context):
    run_workflow(context, workflow())
    if context["batch"]:
        return

    print(f"Checking at: {datetime.now()}")
    schedule.every(10).minutes.do(functools.partial(run_on_schedule, context))
    while True:
        schedule.run_pending()
        time.sleep(10 * 60)


if __name__ == "__main__":
    print("Running Muninn-Storage")
    args = parse_args()
    setup_logging(args.verbose)
    context = args.__dict__
    main(context)
