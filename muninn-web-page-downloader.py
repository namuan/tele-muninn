#!/usr/bin/env python3
"""
Download web page using puppeteer and save it to local file system
"""
import functools
import logging
import time
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from datetime import datetime
from pathlib import Path
from typing import Dict, Union

import dataset
import schedule
from dataset.table import Table
from dotenv import load_dotenv
from py_executable_checklist.workflow import WorkflowBase, run_command, run_workflow
from slug import slug

from common_utils import fetch_html_page, html_parser_from, setup_logging

load_dotenv()

OUTPUT_DIR = Path.home().joinpath("OutputDir", "tele-bookmarks", "web-to-pdf")


class ConnectToDatabase(WorkflowBase):
    """
    Connect to database
    """

    database_file_path: Path

    def execute(self) -> dict:
        db_connection_string = f"sqlite:///{self.database_file_path.as_posix()}"
        db = dataset.connect(db_connection_string)
        bookmarks_table = db.create_table("bookmarks")

        return {"db_table": bookmarks_table}


class SelectPendingBookmarksToDownload(WorkflowBase):
    """
    Select next batch of bookmarks to download
    """

    db_table: Table

    def execute(self) -> dict:
        logging.info("Selecting next batch of files to download from %s table", self.db_table.name)
        web_pages = self.db_table.find(source="WebPage", content=None, _limit=1)
        bookmarked_urls = {web_page["id"]: web_page["note"] for web_page in web_pages}
        return {"bookmarked_urls": bookmarked_urls}


class DownloadWebPages(WorkflowBase):
    """
    Download selected web pages to local directory and update database
    """

    bookmarked_urls: Dict[str, str]
    db_table: Table

    def handle_web_page(self, web_page_url: str) -> Union[Path, str]:
        page_html = fetch_html_page(web_page_url)
        bs = html_parser_from(page_html)
        web_page_title = slug(bs.title.string if bs.title and bs.title.string else web_page_url)
        target_file = OUTPUT_DIR / f"{web_page_title}.pdf"
        cmd = f'./webpage_to_pdf.py -i "{web_page_url}" -o "{target_file}" --headless'
        run_command(cmd)
        if target_file.exists():
            return target_file
        else:
            logging.error("Failed to generate PDF for %s", web_page_url)
            return "Not downloaded"

    def execute(self):
        logging.info("Downloading [%s] web pages", len(self.bookmarked_urls))
        for db_id, webpage_url in self.bookmarked_urls.items():
            print(f"Downloading {webpage_url}")
            downloaded_file_path_or_error = self.handle_web_page(webpage_url)
            print(f"Updating database with local id {db_id} -> download file: {downloaded_file_path_or_error}")
            self.db_table.update({"id": db_id, "content": downloaded_file_path_or_error}, ["id"])


def workflow():
    return [
        ConnectToDatabase,
        SelectPendingBookmarksToDownload,
        DownloadWebPages,
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


def run_on_schedule(context):
    run_workflow(context, workflow())


def main(context):
    if context["batch"]:
        run_workflow(context, workflow())
        return

    print(f"Checking at: {datetime.now()}")
    schedule.every(10).minutes.do(functools.partial(run_on_schedule, context))
    while True:
        schedule.run_pending()
        time.sleep(10 * 60)


if __name__ == "__main__":
    print("Running Muninn-WebPage-Downloader")
    args = parse_args()
    setup_logging(args.verbose)
    context = args.__dict__
    main(context)
