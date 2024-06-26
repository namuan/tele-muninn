#!/usr/bin/env python3
"""
Fetch tweets from a list of twitter accounts and send the tweets to a telegram group
It also generates a chart for the stock symbol mentioned in the tweet
"""
import logging
import os
import time
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from pathlib import Path

from peewee import (
    BigIntegerField,
    CharField,
    DateTimeField,
    Model,
    SqliteDatabase,
    UUIDField,
)

from common_utils import (
    build_chart_links_for,
    search_rgx,
    send_message_to_telegram,
    uuid_gen,
)
from twit_api import get_twitter_user_timeline

home_dir = os.getenv("HOME")
db = SqliteDatabase(home_dir + "/twitter_pumps.db")

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")


class TweetData(Model):
    id = UUIDField(primary_key=True)
    twitter_handle = CharField()
    symbol = CharField()
    timestamp = BigIntegerField()
    tweet_id = CharField()
    tweet = CharField()
    posted_at = DateTimeField(null=True)

    class Meta:
        database = db

    @staticmethod
    def save_from(twitter_handle, symbol, tweet, tweet_id, posted_at):
        entity = dict(
            id=uuid_gen(),
            timestamp=time.time(),
            twitter_handle=twitter_handle,
            tweet_id=tweet_id,
            symbol=symbol,
            tweet=tweet,
            posted_at=posted_at,
        )
        TweetData.insert(entity).execute()


TweetData.create_table()


def save_data(tweet_data):
    TweetData.save_from(**tweet_data)


def tweet_already_processed(current_tweet_id):
    selected_tweet = TweetData.get_or_none(TweetData.tweet_id == current_tweet_id)
    return selected_tweet is not None


def fetch_recent_tweets(acct):
    print(f"Fetching last tweet from account {acct}")
    return get_twitter_user_timeline(acct)


def extract_tweet_id(new_tweet):
    return new_tweet.id


def extract_tweet_time(recent_tweet):
    return recent_tweet.created_at


def extract_symbols(new_tweet):
    tweet = new_tweet.text
    symbols = search_rgx(tweet, r"\$([a-zA-Z]+)")
    print(f"Extracted {symbols} stock symbol from {tweet}")
    return tweet, [s.lower() for s in symbols]


def flatten_list(given_list):
    return [item for item in given_list]


def collect_symbols_from_tweets(twitter_accounts):
    symbols = []
    for acct in twitter_accounts:
        if acct.startswith("#"):
            continue

        try:
            recent_tweets = fetch_recent_tweets(acct)
            for recent_tweet in recent_tweets:
                tweet_id = extract_tweet_id(recent_tweet)
                raw_posted_dt = extract_tweet_time(recent_tweet)
                if tweet_already_processed(tweet_id):
                    print(
                        f"Old Tweet from {recent_tweet.user.name} at {raw_posted_dt} -> {tweet_id} - already processed"
                    )
                    continue
                else:
                    print(f"New Tweet from {recent_tweet.user.name} at {raw_posted_dt} -> {tweet_id}")

                tweet, symbols_from_message = extract_symbols(recent_tweet)
                if not tweet.startswith("RT") and symbols_from_message:
                    for symbol in flatten_list(symbols_from_message):
                        entity = dict(
                            twitter_handle=recent_tweet.user.name,
                            symbol=symbol,
                            tweet=tweet,
                            tweet_id=tweet_id,
                            posted_at=raw_posted_dt,
                        )
                        symbols.append(entity)
                        save_data(entity)
        except Exception as e:
            print(f"An error collecting symbols from twitter account {recent_tweet.user.name}")
            print(e)

        time.sleep(poll_freq_in_secs)
    return symbols


def main(twitter_accounts, poll_freq_in_secs):
    symbols = collect_symbols_from_tweets(twitter_accounts)
    print("==> Collected symbols: {}".format([s.get("symbol") for s in symbols]))
    symbols_already_processed = []
    for symbol_mention in symbols:
        symbol = symbol_mention.get("symbol")
        if symbol in symbols_already_processed:
            continue
        symbols_already_processed.append(symbol)

        mention_acct = symbol_mention.get("twitter_handle")
        mention_tweet_id = symbol_mention.get("tweet_id")
        tweet_posted_date = symbol_mention.get("posted_at")
        formatted_posted_dt = tweet_posted_date.strftime("%H:%M(%d %B)")

        try:
            daily_chart, _, message = build_chart_links_for(symbol)
            header = f"""🚀 #*{symbol}* 👀 posted by [{mention_acct}](https://twitter.com/{mention_acct}/status/{mention_tweet_id}) at {formatted_posted_dt}"""
            send_message_to_telegram(BOT_TOKEN, GROUP_CHAT_ID, header, disable_web_preview=False)
            send_message_to_telegram(
                BOT_TOKEN,
                GROUP_CHAT_ID,
                daily_chart,
                format="HTML",
                disable_web_preview=False,
            )
            send_message_to_telegram(BOT_TOKEN, GROUP_CHAT_ID, message)
            print(f"Sent message by {mention_acct} for {symbol}")
        except Exception:
            logging.exception("Something went wrong")
        time.sleep(poll_freq_in_secs)


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
    twitter_accounts = Path("twitter_furus_accounts.txt").read_text().splitlines()
    poll_freq_in_secs = 5
    while True:
        try:
            main(twitter_accounts, poll_freq_in_secs)
        except Exception as e:
            print("🚨🚨🚨 Something went wrong")
            print(e)
