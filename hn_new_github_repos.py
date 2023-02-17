#!/usr/bin/env python3
"""
Find Links to Github/GitLab and Bitbucket from HN new news
Send links over Telegram

Usage:
./hn_new_github_repos.py -h
"""

import argparse
import logging
import os
from argparse import ArgumentParser
from typing import List

import dataset
from dataset import Table
from dotenv import load_dotenv
from py_executable_checklist.workflow import WorkflowBase

from common_utils import (
    fetch_html_page,
    html_parser_from,
    run_in_background,
    send_message_to_telegram,
    setup_logging,
)

# Common functions across steps
load_dotenv()

DEFAULT_BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")
DB_FILE = "hn_new_github_repos.db"


# Workflow steps


class GrabHackerNewsPage(WorkflowBase):
    """
    Grab HackerNews new page
    """

    def execute(self):
        try:
            page_html = fetch_html_page("https://news.ycombinator.com/newest")
        except Exception:
            logging.warning("Unable to fetch Hackernews page")
            return {"hn_newest_html": "<html></html>"}

        return {"hn_newest_html": page_html}


class ExtractLinks(WorkflowBase):
    """
    Select links from HTML
    """

    hn_newest_html: str

    def execute(self):
        bs = html_parser_from(self.hn_newest_html)
        return {"all_links": [link.get("href") for link in bs.find_all("a", href=True)]}


class SelectRepoLinks(WorkflowBase):
    """
    Extract repo links from the list of links
    """

    all_links: List[str]

    def interested_in(self, link):
        known_domains = ["github.com", "gitlab.com", "bitbucket.com"]

        def has_known_domain(post_link):
            return any(map(lambda link: link in post_link.lower(), known_domains))

        return link.startswith("http") and has_known_domain(link)

    def execute(self):
        logging.info(f"SelectRepoLinks: {len(self.all_links)}")
        return {"repo_links": [link for link in self.all_links if self.interested_in(link)]}


class SendToTelegram(WorkflowBase):
    """
    Send links as telegram messages
    """

    saved_repo_links: List[str]

    def execute(self):
        logging.info(f"SendToTelegram: {len(self.saved_repo_links)}")
        for link in self.saved_repo_links:
            if "HackerNews/API" not in link:
                try:
                    send_message_to_telegram(DEFAULT_BOT_TOKEN, GROUP_CHAT_ID, link, disable_web_preview=False)
                    logging.info(f"Sent {link}")
                except Exception as e:
                    error_message = f"Unable to send {link} to Telegram: {e}"
                    logging.error(error_message)


class FilterExistingLinks(WorkflowBase):
    """
    Ignore links already stored in the database
    """

    repo_links: List[str]
    db_table: Table

    def _in_database(self, repo_link):
        return self.db_table.find_one(repo_link=repo_link)

    def execute(self):
        logging.info(f"FilterExistingLinks: {len(self.repo_links)}")
        return {"new_repo_links": [link for link in self.repo_links if not self._in_database(link)]}


class SaveLinks(WorkflowBase):
    """
    Save links in the database
    """

    new_repo_links: List[str]
    db_table: Table

    def execute(self):
        logging.info(f"SaveLinks: {len(self.new_repo_links)}")
        for link in self.new_repo_links:
            entry_row = {
                "repo_link": link,
            }
            self.db_table.insert(entry_row)
            logging.info(f"Updated database: {entry_row}")

        return {"saved_repo_links": self.new_repo_links}


class SetupDatabase(WorkflowBase):
    """
    Set up SQLite database
    """

    def execute(self):
        home_dir = os.getenv("HOME")
        table_name = "hn_repo_links"
        db_connection_string = f"sqlite:///{home_dir}/{DB_FILE}"
        db = dataset.connect(db_connection_string)
        logging.info(f"Connecting to database {db_connection_string} and table {table_name}")
        return {"db_table": db.create_table(table_name)}


def workflow():
    return [
        SetupDatabase,
        GrabHackerNewsPage,
        ExtractLinks,
        SelectRepoLinks,
        FilterExistingLinks,
        SaveLinks,
        SendToTelegram,
    ]


def parse_args():
    parser = ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
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
    print("Running HN GitHub Repos")
    args = parse_args()
    setup_logging(args.verbose)
    context = args.__dict__
    run_in_background(context, workflow())
