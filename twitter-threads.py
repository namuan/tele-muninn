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
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List

import requests
from py_executable_checklist.workflow import WorkflowBase, run_workflow
from snscrape.modules.twitter import (
    Tweet,
    TwitterTweetScraper,
    TwitterTweetScraperMode,
    TwitterUserScraper,
)
from tweepy.models import Status

from common_utils import setup_logging
from twitter_api import get_tweets_by_id

# Common functions across steps

# Workflow steps


class ExtractInfoFromTweetUrl(WorkflowBase):
    """
    Extract tweet ID, username, and other info from tweet URL
    """

    tweet_url: str
    output_dir: Path

    def execute(self):
        username = self.tweet_url.split("/")[3]
        tweet_id = int(self.tweet_url.split("/")[5])

        tweet_output_folder = self.output_dir.joinpath(str(tweet_id))
        tweet_output_folder.mkdir(parents=True, exist_ok=True)

        return {"tweet_id": tweet_id, "username": username, "tweet_output_folder": tweet_output_folder}


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
        return {"tweet_owner": main_tweet.user.username}


class FetchAllTweetsUsingSearch(WorkflowBase):
    """
    Fetch all tweets on a particular date
    """

    tweet_owner: str
    tweet_id: str

    def username_from_reply_to_user(self, reply_to_user):
        if reply_to_user:
            return reply_to_user.username.lower()
        else:
            return None

    def collect_tweets_in_thread(self, recent_tweets, user_from_thread_url, tweet_id_from_thread_url):
        tweets_in_thread = {}
        for tweet in recent_tweets:
            if tweet.id == tweet_id_from_thread_url:
                tweets_in_thread[tweet.id] = tweet

            if tweet.conversationId == tweet_id_from_thread_url:
                tweet_is_a_reply_to_same_user = (
                    self.username_from_reply_to_user(tweet.inReplyToUser) == user_from_thread_url
                )
                if tweet_is_a_reply_to_same_user:
                    tweets_in_thread[tweet.id] = tweet

        return tweets_in_thread

    def collect_recent_tweets(self, user_from_thread_url, tweets_to_fetch):
        collected_tweets = []
        for tweet in TwitterUserScraper(user_from_thread_url).get_items():
            if len(collected_tweets) == tweets_to_fetch:
                break
            else:
                collected_tweets.append(tweet)

        return collected_tweets

    def execute(self):
        all_tweets = self.collect_recent_tweets(self.tweet_owner, 100)
        tweets_in_thread = self.collect_tweets_in_thread(all_tweets, self.tweet_owner.lower(), self.tweet_id)
        return {"incomplete_tweets_in_thread": tweets_in_thread}


class CollectAllTweetsUsingApi(WorkflowBase):
    """
    Collect all tweets from a particular user's timeline using Twitter API
    """

    incomplete_tweets_in_thread: Dict[str, Tweet]

    def execute(self):
        tweets_in_thread = get_tweets_by_id(list(self.incomplete_tweets_in_thread.keys()))
        # output
        return {"tweets_in_thread": tweets_in_thread}


class CollectAllMediaLinks(WorkflowBase):
    """
    Download all images linked in a set of tweets
    """

    tweets_in_thread: List[Any]

    def media_from_tweet(self, tweet):
        if "media" in tweet.entities:
            for image in tweet.entities["media"]:
                yield (image["media_url"])

    def execute(self):
        tweet_to_media_links = {}
        for tweet in self.tweets_in_thread:
            tweet_to_media_links[tweet.id] = [i for i in self.media_from_tweet(tweet)]

        return {"tweet_to_media_links": tweet_to_media_links}


class DownloadAllMediaFiles(WorkflowBase):
    """
    Download all videos linked in a set of tweets
    """

    tweet_to_media_links: Dict[str, List[str]]
    tweet_output_folder: Path

    def download_file(self, url: str) -> str:
        response = requests.get(url)
        file_name = url.split("/")[-1]
        file_path = self.tweet_output_folder / file_name
        with open(file_path, "wb") as file:
            file.write(response.content)
        return file_name

    def unwrap_list_of_lists(self, list_of_lists):
        return [item for sublist in list_of_lists for item in sublist]

    def execute(self):
        with ThreadPoolExecutor() as executor:
            download_mapping = {
                url: executor.submit(self.download_file, url).result()
                for url in self.unwrap_list_of_lists(self.tweet_to_media_links.values())
            }
        return {"download_mapping": download_mapping}


class GenerateOutputMarkdown(WorkflowBase):
    """
    Generate Markdown output based on collected tweet data
    """

    tweets_in_thread: List[Status]
    tweet_to_media_links: Dict[str, List[str]]
    download_mapping: Dict[str, str]
    tweet_output_folder: Path

    def format_tweet(self, tweet: Status) -> str:
        user = tweet.user.screen_name
        text = tweet.full_text
        date_time = tweet.created_at.strftime("%Y-%m-%d %H:%M:%S")
        media_links = self.tweet_to_media_links.get(tweet.id, [])
        media_md = "\n".join(f"![{Path(i).name}]({self.download_mapping[i]})" for i in media_links)
        return f"{user} ({tweet.user.name})\n\n{text}\n\n{media_md}\n{date_time}\n\n----\n"

    def execute(self):
        sorted_tweets = sorted(self.tweets_in_thread, key=lambda t: t.id)
        output_md = "".join(self.format_tweet(tweet) for tweet in sorted_tweets)
        output_file = self.tweet_output_folder / "output.md"
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(output_md)
        return {"md_file_path": output_file}


def workflow():
    return [
        ExtractInfoFromTweetUrl,
        FetchTweetData,
        FetchAllTweetsUsingSearch,
        CollectAllTweetsUsingApi,
        CollectAllMediaLinks,
        DownloadAllMediaFiles,
        GenerateOutputMarkdown,
    ]


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
    output_file = context["md_file_path"]
    print(f"Output file: {output_file}")


if __name__ == "__main__":  # pragma: no cover
    main()
