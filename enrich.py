import os
from bs4 import BeautifulSoup
import re
import requests
import json
import logging
import aws_lambda
from urllib.parse import urlparse
from main import DEV_MODE



def enrich_twitter_bookmarks(twitter_bookmarks):
  
  twitter_bookmarks = retrieve_tweets_html(twitter_bookmarks)

  # Extract a title and author and add them to the dict
  for bkmk in twitter_bookmarks:
    bkmk["title"], bkmk["author"] = get_tweet_title_author(bkmk)
  
  return twitter_bookmarks



def retrieve_tweets_html(twitter_bookmarks):
  # Build list of Tweet IDs
  tweet_ids_list = \
  [
    {
      "notion_id": bkmk["notion_id"], 
      "tweet_id": get_tweet_id(bkmk)
    } for bkmk in twitter_bookmarks
  ]

  # Build list of Tweet widget URL
  tweet_widget_urls_list = \
  [
    {
      "notion_id": item['notion_id'], 
      "tweet_widget_url": get_tweet_widget_url(item['tweet_id'])
    } for item in tweet_ids_list
  ]

  # Prepare the payload
  payload = {
    "tweets": tweet_widget_urls_list,
    "mode": DEV_MODE
  }
  
  # Prepare the scraping lambda query
  body = json.dumps(payload)
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


def enrich_linkedin_bookmarks(linkedin_bookmarks):
  for bkmk in linkedin_bookmarks:
    bkmk['html_content'] = retrieve_page_html(bkmk)
    bkmk['author'], bkmk['title'], bkmk['image_url'] = get_linkedin_data(bkmk)

  return linkedin_bookmarks

def retrieve_page_html(bkmk):
  response = requests.get(bkmk["url"])
  response.raise_for_status()  # Check if the request was successful
  return response.text  # Return the HTML content of the page

def get_linkedin_data(bkmk):
  soup = BeautifulSoup(bkmk["html_content"], 'html.parser')
  author = "Not found"
  title = "Undefined"
  image_url = None

  logging.debug(f"LinkedIn bkmk: {bkmk}")
  
  # Extract the author
  actor_tag = soup.find('a', {'data-tracking-control-name': 'public_post_feed-actor-name'})
  
  if actor_tag is not None:
      author = actor_tag.text.strip()
  logging.debug(f"author extracted: {author}")
  
  # Extract title
  content = soup.find(attrs={'data-test-id':'main-feed-activity-card__commentary'})
  
  if content is not None:
    title = content.get_text().split('\n', 1)[0]

  logging.debug(f"title extracted: {title}")

  # Extract image
  image_container = soup.find(attrs={'data-test-id':'feed-images-content'})

  if image_container is not None:
    img_tag = image_container.find('img', attrs={'data-delayed-url': True})
    if img_tag is not None: 
      image_url = img_tag['data-delayed-url']

  
  return author, title, image_url




def enrich_youtube_bookmarks(youtube_bookmarks):
  for bkmk in youtube_bookmarks:
    bkmk['html_content'] = retrieve_page_html(bkmk)
    bkmk['author'], bkmk['title'], bkmk['image_url'] = get_youtube_data(bkmk)

  return youtube_bookmarks

def get_youtube_data(bkmk):
  soup = BeautifulSoup(bkmk["html_content"], 'html.parser')
  author = "Not found"
  title = "Undefined"
  image_url = None

  # Extract author
  author_tag = soup.find(attrs={'itemprop':'author'}).find('link', {'itemprop':'name'})

  if author_tag is not None:
    author = author_tag['content']

  # Extract title
  title_tag = soup.find(attrs={'property':'og:title'})

  if title_tag is not None:
    title = title_tag['content']

  # Extract image
  image_tag = soup.find(attrs={'property':'og:image'})

  if image_tag is not None:
    image_url = image_tag['content']

  return author, title, image_url




def enrich_other_bookmarks(other_bookmarks):
  for bkmk in other_bookmarks:
    bkmk['html_content'] = retrieve_page_html(bkmk)
    bkmk['author'], bkmk['title'], bkmk['image_url'], bkmk['summary']= get_article_data(bkmk)

  return other_bookmarks

def get_article_data(bkmk):
  soup = BeautifulSoup(bkmk["html_content"], 'html.parser')
  author = ""
  title = "Undefined"
  image_url = None
  summary = None

  

  