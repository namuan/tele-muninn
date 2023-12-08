#!/usr/bin/env python3
"""
Download video from tweet url
"""
import json
import re
import sys
from argparse import ArgumentParser, RawDescriptionHelpFormatter

import requests

genericUserAgent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
)


def best_quality(arr):
    videos = [v for v in arr if v["content_type"] == "video/mp4"]
    return sorted(videos, key=lambda x: int(x.get("bitrate", 0)), reverse=True)[0]["url"]


def extract_tweet_id(url):
    match = re.search(r"/status/(\d+)", url)
    return match.group(1) if match else None


def main(url):
    tweet_id = extract_tweet_id(url)
    if not tweet_id:
        return {"error": "Invalid URL or Tweet ID not found"}

    obj = {"id": tweet_id}

    headers = {
        "user-agent": genericUserAgent,
        "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
        "host": "api.twitter.com",
        "x-twitter-client-language": "en",
        "accept-language": "en",
    }

    activate_url = "https://api.twitter.com/1.1/guest/activate.json"
    graphql_tweet_url = "https://twitter.com/i/api/graphql/5GOHgZe-8U2j5sVHQzEm9A/TweetResultByRestId"

    response = requests.post(activate_url, headers=headers)
    if response.status_code != 200:
        return {"error": "ErrorCouldntFetch"}

    req_act = response.json()
    headers["host"] = "twitter.com"
    headers["content-type"] = "application/json"
    headers["x-guest-token"] = req_act["guest_token"]
    headers["cookie"] = f"guest_id=v1%3A{req_act['guest_token']}"

    # Query building
    query = {
        "variables": {
            "tweetId": obj["id"],
            "withCommunity": False,
            "includePromotedContent": False,
            "withVoice": False,
        },
        "features": {
            "creator_subscriptions_tweet_preview_api_enabled": True,
            "c9s_tweet_anatomy_moderator_badge_enabled": True,
            "tweetypie_unmention_optimization_enabled": True,
            "responsive_web_edit_tweet_api_enabled": True,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
            "view_counts_everywhere_api_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "responsive_web_twitter_article_tweet_consumption_enabled": False,
            "tweet_awards_web_tipping_enabled": False,
            "responsive_web_home_pinned_timelines_enabled": True,
            "freedom_of_speech_not_reach_fetch_enabled": True,
            "standardized_nudges_misinfo": True,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
            "longform_notetweets_rich_text_read_enabled": True,
            "longform_notetweets_inline_media_enabled": True,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "responsive_web_media_download_video_enabled": False,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "responsive_web_enhance_cards_enabled": False,
        },
    }

    # Encoding the query parameters
    query_str = (
        f"{graphql_tweet_url}?variables={json.dumps(query['variables'])}&features={json.dumps(query['features'])}"
    )

    response = requests.get(query_str, headers=headers)
    if response.status_code != 200:
        return {"error": "ErrorTweetUnavailable"}

    tweet = response.json()

    # Process the tweet data
    base_tweet = tweet.get("data", {}).get("tweetResult", {}).get("result", {}).get("legacy", {})

    base_media = None
    if (
        "retweeted_status_result" in base_tweet
        and "extended_entities" in base_tweet["retweeted_status_result"]["result"]["legacy"]
    ):
        base_media = base_tweet["retweeted_status_result"]["result"]["legacy"]["extended_entities"]
    elif "extended_entities" in base_tweet:
        base_media = base_tweet["extended_entities"]

    if not base_media or "media" not in base_media:
        return {"error": "ErrorNoVideosInTweet"}

    media = [i for i in base_media["media"] if i["type"] in ["video", "animated_gif"]]

    if not media:
        return {"error": "ErrorNoVideosInTweet"}

    single, multiple = None, []
    if len(media) > 1:
        for i, item in enumerate(media):
            multiple.append(
                {
                    "type": "video",
                    "thumb": item["media_url_https"],
                    "url": {  # Replace with your Python equivalent
                        "service": "twitter",
                        "type": "remux",
                        "u": best_quality(item["video_info"]["variants"]),
                        "filename": f"twitter_{obj['id']}_{i + 1}.mp4",
                    },
                }
            )
    elif len(media) == 1:
        single = best_quality(media[0]["video_info"]["variants"])

    if single:
        return {
            "type": "remux",
            "urls": single,
            "filename": f"twitter_{obj['id']}.mp4",
            "audioFilename": f"twitter_{obj['id']}_audio",
        }
    elif multiple:
        return {"picker": multiple}
    else:
        return {"error": "ErrorNoVideosInTweet"}


def download_video(url, filename):
    try:
        print(f"Downloading {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()  # This will raise an HTTPError if the HTTP request returned an unsuccessful status code

        with open(filename, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive new chunks
                    file.write(chunk)
        return f"Video downloaded successfully as {filename}"
    except requests.exceptions.RequestException as e:
        return f"An error occurred: {e}"


def parse_args():
    parser = ArgumentParser(description=__doc__, formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument("-i", "--input", type=str, required=True, help="Twitter Url")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    input_url = args.input
    output = main(input_url)
    if output["error"]:
        print(f"Unable to download video from {input_url} - {output['error']}")
        sys.exit(-1)

    result = download_video(output["urls"], output["filename"])
    print(result)
