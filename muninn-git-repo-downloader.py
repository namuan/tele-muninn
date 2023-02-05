#!/usr/bin/env python3
"""
Download the snapshot of GitHub repos as a zip file and save it to local file system
"""
import logging
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pathlib import Path
from typing import Dict, List, Type, Union

import requests
from dotenv import load_dotenv
from py_executable_checklist.workflow import WorkflowBase

from common_utils import run_in_background, setup_logging, table_from
from tele_bookmark_bot import GitHub

load_dotenv()

OUTPUT_DIR = Path.home().joinpath("OutputDir", "tele-bookmarks", "web-to-pdf")


class SelectPendingBookmarksToDownload(WorkflowBase):
    """
    Select next batch of bookmarks to download
    """

    database_file_path: Path

    def execute(self) -> dict:
        with table_from(self.database_file_path) as db_table:
            logging.info("Selecting next batch of GH repos to download from %s table", db_table.name)
            github_repos = db_table.find(source=GitHub.__name__, content=None)
            bookmarked_repos = {gh_repo["id"]: gh_repo["note"] for gh_repo in github_repos}

        return {"bookmarked_repos": bookmarked_repos}


class DownloadGitRepo(WorkflowBase):
    """
    Download selected web pages to local directory and update database
    """

    bookmarked_repos: Dict[str, str]
    database_file_path: Path

    def download_file(self, file_name: str, file_url: str) -> Union[Path, str]:
        target_file = OUTPUT_DIR / f"{file_name}.zip"
        if target_file.exists():
            return target_file

        url = file_url + "main.zip"
        response = requests.get(url)
        if response.status_code != 200:
            url = file_url + "master.zip"
            response = requests.get(url)

        with open(target_file, "wb") as file:
            file.write(response.content)

        if target_file.exists():
            return target_file
        else:
            logging.error("Failed to download zip for %s", file_url)
            return "Not downloaded"

    def build_zip_file_path_from(self, gh_repo_url) -> str:
        return gh_repo_url + "/archive/refs/heads/"

    def content_from(self, downloaded_file_path_or_error: Union[Path, str]) -> str:
        if isinstance(downloaded_file_path_or_error, Path):
            return downloaded_file_path_or_error.as_posix()
        else:
            return downloaded_file_path_or_error

    def execute(self):
        logging.info("Downloading [%s] web pages", len(self.bookmarked_repos))
        for db_id, gh_repo in self.bookmarked_repos.items():
            logging.info(f"Downloading {gh_repo}")
            repo_zip_file = self.build_zip_file_path_from(gh_repo)
            target_file_name = Path(gh_repo).name
            local_zip_file = self.download_file(target_file_name, repo_zip_file)
            logging.info(f"Updating database with local id {db_id} -> download file: {local_zip_file}")
            with table_from(self.database_file_path) as db_table:
                db_table.update({"id": str(db_id), "content": self.content_from(local_zip_file)}, ["id"])


def workflow() -> List[Type[WorkflowBase]]:
    return [
        SelectPendingBookmarksToDownload,
        DownloadGitRepo,
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
    print("Running Muninn-GitRepo-Downloader")
    args = parse_args()
    setup_logging(args.verbose)
    context = args.__dict__
    run_in_background(context, workflow())
