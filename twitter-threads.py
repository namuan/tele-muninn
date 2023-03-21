#!/usr/bin/env python3
"""
Download all tweets given a Twitter thread and archive them in a single HTML file.
The input is a URL to the first tweet in the thread.
The output is a directory where everything downloaded is stored. The HTML file is named with the tweet user and tweet id.
Eg:
./twitter-threads.py -i https://twitter.com/elonmusk/status/1320000000000000000 -o output_dir
"""
import logging
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pathlib import Path
from typing import Any, Dict, List

from py_executable_checklist.workflow import WorkflowBase, run_workflow
from snscrape.modules.twitter import (
    Tweet,
    TwitterSearchScraper,
    TwitterTweetScraper,
    TwitterTweetScraperMode,
)

from common_utils import setup_logging

# Common functions across steps

# Workflow steps


class ExtractInfoFromTweetUrl(WorkflowBase):
    """
    Extract tweet ID, username, and other info from tweet URL
    """

    tweet_url: str

    def execute(self):
        username = self.tweet_url.split("/")[3]
        tweet_id = int(self.tweet_url.split("/")[5])
        # output
        return {"tweet_id": tweet_id, "username": username}


class FetchTweetData(WorkflowBase):
    """
    Fetch data for a single tweet using Twitter API
    """

    tweet_id: str

    def execute(self):
        main_tweet: Tweet = next(
            TwitterTweetScraper(mode=TwitterTweetScraperMode.SINGLE, tweetId=self.tweet_id).get_items(), None
        )
        logging.debug("Found main tweet: %s", main_tweet)
        return {"main_tweet": main_tweet, "search_query": ""}


class FetchAllTweetsUsingSearch(WorkflowBase):
    """
    Fetch all tweets on a particular date
    """

    search_query: str

    def execute(self):
        all_tweets = TwitterSearchScraper(query=self.search_query, maxTweets=1000).get_items()

        # output
        return {"all_tweets": all_tweets}


class CollectAllTweetsUsingApi(WorkflowBase):
    """
    Collect all tweets from a particular user's timeline using Twitter API
    """

    username: str

    def execute(self):
        # code to fetch all tweets
        all_tweets = ...
        # output
        return {"all_tweets": all_tweets}


class DownloadAllLinkedImages(WorkflowBase):
    """
    Download all images linked in a set of tweets
    """

    tweets: List[str]

    def execute(self):
        # code to download all images
        downloaded_images = ...
        # output
        return {"downloaded_images": downloaded_images}


class DownloadAllLinkedVideos(WorkflowBase):
    """
    Download all videos linked in a set of tweets
    """

    tweets: List[str]

    def execute(self):
        # code to download all videos
        downloaded_videos = ...
        # output
        return {"downloaded_videos": downloaded_videos}


class GenerateOutputHtml(WorkflowBase):
    """
    Generate HTML output based on collected tweet data
    """

    tweet_data: List[Dict[str, Any]]

    def execute(self):
        # code to generate HTML output
        html_output = ...
        # output
        return {"html_output": html_output}


def workflow():
    return [
        ExtractInfoFromTweetUrl,
        FetchTweetData,
        FetchAllTweetsUsingSearch,
        CollectAllTweetsUsingApi,
        DownloadAllLinkedImages,
        DownloadAllLinkedVideos,
        GenerateOutputHtml,
    ]


# Boilerplate


def parse_args():
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("-i", "--tweet_url", type=str, required=True, help="URL to the first tweet in the thread"),
    parser.add_argument("-o", "--output-dir", type=Path, required=True, help="Output directory"),
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        dest="verbose",
        help="Increase verbosity of logging output. Display context variables between each step run",
    )
    return parser.parse_args()


def main() -> None:  # pragma: no cover
    args = parse_args()
    setup_logging(args.verbose)
    context = args.__dict__
    run_workflow(context, workflow())


if __name__ == "__main__":  # pragma: no cover
    main()
