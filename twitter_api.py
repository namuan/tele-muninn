import logging
import os
import time
from typing import List

import tweepy
from dotenv import load_dotenv
from tweepy.models import Status

load_dotenv()

# Twitter
TWITTER_CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY")
TWITTER_CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET")
TWITTER_ACCESS_TOKEN_KEY = os.getenv("TWITTER_ACCESS_TOKEN_KEY")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN_KEY, TWITTER_ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)


def get_twitter_user_timeline(user_acct):
    return api.user_timeline(user_acct, count=50)


def get_tweet(tweet_id):
    return with_limit_handled(lambda: api.get_status(id=tweet_id))


def get_tweets_by_id(tweet_ids) -> List[Status]:
    """Retrieve tweets by their ID"""
    tweets = []
    try:
        # Split tweet IDs into chunks of 100, since API.lookup_statuses() can retrieve up to 100 tweets at once
        id_chunks = [tweet_ids[i : i + 100] for i in range(0, len(tweet_ids), 100)]

        # Retrieve tweets for each ID chunk
        for id_chunk in id_chunks:
            tweets.extend(api.lookup_statuses(id=id_chunk, tweet_mode="extended"))
    except tweepy.TweepyException as e:
        print("Error fetching tweets: ", e)

    return tweets


def get_twitter_home_timeline():
    return with_limit_handled(lambda: api.home_timeline(count=200, exclude_replies=True))


def with_limit_handled(func):
    try:
        return func()
    except tweepy.client.TooManyRequests:
        logging.warning("Hit Limit, waiting for 15 minutes")
        time.sleep(15 * 60)
        return func()


if __name__ == "__main__":
    print(get_twitter_home_timeline())
