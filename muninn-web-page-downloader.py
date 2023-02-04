#!/usr/bin/env python3
"""
Download web page using puppeteer and save it to local file system
"""
import logging
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pathlib import Path
from typing import Dict, List, Type, Union

from dotenv import load_dotenv
from py_executable_checklist.workflow import WorkflowBase, run_command
from slug import slug

from common_utils import (
    fetch_html_page,
    html_parser_from,
    run_in_background,
    setup_logging,
    table_from,
)
from tele_bookmark_bot import WebPage

load_dotenv()

OUTPUT_DIR = Path.home().joinpath("OutputDir", "tele-bookmarks", "web-to-pdf")


class SelectPendingBookmarksToDownload(WorkflowBase):
    """
    Select next batch of bookmarks to download
    """

    database_file_path: Path

    def execute(self) -> dict:
        with table_from(self.database_file_path) as db_table:
            logging.info("Selecting next batch of files to download from %s table", db_table.name)
            web_pages = db_table.find(source=WebPage.__name__, content=None)
            bookmarked_urls = {web_page["id"]: web_page["note"] for web_page in web_pages}

        return {"bookmarked_urls": bookmarked_urls}


class DownloadWebPages(WorkflowBase):
    """
    Download selected web pages to local directory and update database
    """

    bookmarked_urls: Dict[str, str]
    database_file_path: Path

    def handle_web_page(self, web_page_url: str) -> Union[Path, str]:
        page_html = fetch_html_page(web_page_url)
        bs = html_parser_from(page_html)
        web_page_title = slug(bs.title.string if bs.title and bs.title.string else web_page_url)
        target_file = OUTPUT_DIR / f"{web_page_title}.pdf"
        if target_file.exists():
            logging.info("File %s already exists, skipping", target_file)
            return target_file

        cmd = f'./webpage_to_pdf.py -i "{web_page_url}" -o "{target_file}" --headless'
        run_command(cmd)
        if target_file.exists():
            return target_file
        else:
            logging.error("Failed to generate PDF for %s", web_page_url)
            return "Not downloaded"

    def content_from(self, downloaded_file_path_or_error: Union[Path, str]) -> str:
        if isinstance(downloaded_file_path_or_error, Path):
            return downloaded_file_path_or_error.as_posix()
        else:
            return downloaded_file_path_or_error

    def execute(self):
        logging.info("Downloading [%s] web pages", len(self.bookmarked_urls))
        for db_id, webpage_url in self.bookmarked_urls.items():
            logging.info(f"Downloading {webpage_url}")
            downloaded_file_path_or_error = self.handle_web_page(webpage_url)
            logging.info(f"Updating database with local id {db_id} -> download file: {downloaded_file_path_or_error}")
            with table_from(self.database_file_path) as db_table:
                db_table.update({"id": str(db_id), "content": self.content_from(downloaded_file_path_or_error)}, ["id"])


def workflow() -> List[Type[WorkflowBase]]:
    return [
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


if __name__ == "__main__":
    logging.info("Running Muninn-WebPage-Downloader")
    args = parse_args()
    setup_logging(args.verbose)
    context = args.__dict__
    run_in_background(context, workflow())
