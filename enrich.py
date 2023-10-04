import os
from bs4 import BeautifulSoup
import re
import requests
import json
import logging
import aws_lambda
from urllib.parse import urlparse



def enrich_twitter_bookmarks(twitter_bookmarks):
  
  twitter_bookmarks = retrieve_tweets_html(twitter_bookmarks)

  # Extract a title and author and add them to the dict
  for bkmk in twitter_bookmarks:
    bkmk["title"], bkmk["author"] = get_tweet_title_author(bkmk)
  
  return twitter_bookmarks

def retrieve_tweets_html(twitter_bookmarks):
  # Build list of Tweet IDs
  tweet_ids_list = [{"notion_id": bkmk["notion_id"], "tweet_id": get_tweet_id(bkmk)} for bkmk in twitter_bookmarks]

  # Build list of Tweet widget URL
  tweet_widget_urls_list = [{"notion_id": item['notion_id'], "tweet_widget_url": get_tweet_widget_url(item['tweet_id'])} for item in tweet_ids_list]

  # Prepare the scraping lambda query
  body = json.dumps(tweet_widget_urls_list)
  prepared_request = aws_lambda.prepare_aws_lambda_request(body)

  # The lambda takes the list of dicts and returns the same dict with 2 additional keys for the html content of the tweet and screnshot url on S3
  return requests.Session().send(prepared_request).json()

def get_tweet_id(bkmk):
    # Extract the path and split it into components
    path_components = urlparse(bkmk["url"]).path.split('/')
    
    # The tweet ID is the last component of the path
    tweet_id = path_components[-1] if len(path_components) > 1 else None
    
    return tweet_id

def get_tweet_widget_url(tweet_id):
    return f"https://platform.twitter.com/embed/Tweet.html?id={tweet_id}"

def get_tweet_title_author(bkmk):
  soup = BeautifulSoup(bkmk["html_content"], 'html.parser')
  text = soup.get_text()
  
  # Define the regular expression patterns
  author_pattern = re.compile(r'Twitter Embed(.*?)(?=·|@)')
  title_pattern = re.compile(r'·Follow(.*?)(?=\n|$)', re.DOTALL)
  
  # Search for the patterns in the text
  author_match = author_pattern.search(text)
  title_match = title_pattern.search(text)

  if author_match:
      author = author_match.group(1).strip()
  else:
      author = "Not found"  

  if title_match:
      title = title_match.group(1).strip()
  else:
      title = "Not found"

  return title, author



