import os

from dotenv import load_dotenv
from twikit import Client

load_dotenv()

# Twitter
TWITTER_USERNAME = os.getenv("TWITTER_USERNAME")
TWITTER_EMAIL = os.getenv("TWITTER_EMAIL")
TWITTER_PASSWORD = os.getenv("TWITTER_PASSWORD")

client = Client("en-US")

client.login(auth_info_1=TWITTER_USERNAME, auth_info_2=TWITTER_EMAIL, password=TWITTER_PASSWORD)


def get_twitter_user_timeline(user_acct):
    return client.get_user_tweets(user_acct, tweet_type="Tweets")
