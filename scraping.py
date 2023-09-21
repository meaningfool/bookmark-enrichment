from bs4 import BeautifulSoup
import requests
import json
import logging

def get_tweet_data(tweet_id):
    # Retrieve and return JSON data for a given tweet ID.
    url = f'https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&lang=en'
    logging.debug("Requesting Tweet widget content")
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses

    # Convert HTML response to JSON
    soup = BeautifulSoup(response.content, 'html.parser')
    return json.loads(soup.text)


def extract_tweet_info(data):
    """Extract tweet text and author from JSON data."""
    tweet_text = data.get("text")
    tweet_author = data.get("user", {}).get("name")

    if not tweet_text or not tweet_author:
        logging.error("Expected keys not found in Tweet payload")
        raise ValueError("Expected keys not found in Tweet payload")

    return tweet_text, tweet_author


def parse_tweet_content(tweet_id):
    """Main function to parse tweet content given a tweet ID."""
    data = get_tweet_data(tweet_id)
    return extract_tweet_info(data)
