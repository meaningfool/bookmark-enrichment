import requests
import json
import os
from urllib.parse import urlparse
import logging
from main import DEV_MODE
import utils

NOTION_API_KEY = os.environ['NOTION_API_KEY']

if DEV_MODE == "PROD":
  NOTION_DATABASE_ID = os.environ['NOTION_DATABASE_ID']
else:
  NOTION_DATABASE_ID = os.environ['NOTION_DEV_DATABASE_ID']


headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}


def retrieve_bookmarks_from_notion(nb_bookmarks):
  raw_bookmarks = get_bookmarks_from_notion(nb_bookmarks)
  bookmarks = create_bookmarks_dict(raw_bookmarks)
  return bookmarks


def get_bookmarks_from_notion(page_size):

  ## Build & send the request
  url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"

  filter = {
      "property": "Status",
      "status": {
          "equals": "inbox"
      }
  }

  sorts = [
      {
          "timestamp": "created_time",
          "direction": "ascending"
      }
  ]

  data = {
      "page_size": page_size,
      "filter": filter,
      "sorts": sorts
  }
  response = requests.post(url, headers=headers, data=json.dumps(data))

  ## Raise an error if the bookmarks cannot be retrieved
  if response.status_code != 200:
    custom_message = "Failed to retrieve Notion bookmarks"
    raise requests.HTTPError(f'{response.status_code}: {response.reason}. {custom_message}', response=response)

  return response.json()['results']

def create_bookmarks_dict(notion_raw_bookmarks):
    bookmarks = []
    for item in notion_raw_bookmarks:
        url = item['properties']['URL']['url']
        domain = None if url is None else urlparse(url).netloc
        bookmark = {
            "notion_id": item['id'],
            "url": url,
            "domain": domain
        }
        bookmarks.append(bookmark)
    return bookmarks


def update_bookmark_in_notion(bookmark):
  res1 = update_properties(bookmark)
  res2 = update_children(bookmark)
  update_status(bookmark)
  
  
  return res1, res2

def update_properties(bookmark):
  url = f"https://api.notion.com/v1/pages/{bookmark['notion_id']}"

  name_json = {
    "Name": {
        "title": [
            {
                "type": "text", 
                "text": { 
                    "content": bookmark["title"]
                }
            }
        ]
    }
  }
  
  author_json = {}
  if bookmark.get("author"):
    author_json = {
      "Author": {
          "rich_text": [
              {
                  "type": "text",
                  "text": {
                      "content": bookmark["author"]
                  }
              }
          ]
      }
    }
  
  data = {
    "properties": name_json | author_json
  }
  
  res = requests.patch(url, json=data, headers=headers)
  return res

def update_children(bookmark):

  url = f"https://api.notion.com/v1/blocks/{bookmark['notion_id']}/children"
  children = []

  if bookmark.get("image_url"):
    image_url = utils.get_image_url(bookmark.get("image_url"))
    child = {
      "object": "block",
      "type": "image",
      "image": {
        "type": "external",
        "external": {
          "url": image_url
        }
      }
    }
    children.append(child)
    
  if bookmark.get("summary"):
    child = {
      "object": "block",
      "type": "paragraph",
      "paragraph": {
          "rich_text": [
              {
              "type": "text",
              "text": {
                "content": bookmark.get("summary"),
                "link": None
                  }
              }
          ]
      }
    }
    children.append(child)

  data = {}
  if len(children) > 0:
    data = {
      "children": children
    }

  res = requests.patch(url, json=data, headers=headers)
  return res


def update_status(bookmark):
    url = f"https://api.notion.com/v1/pages/{bookmark['notion_id']}"

    data = {
        "properties": {
            "Status": {
                "status": {
                        "name": "AIprocessed"
                }
            }
        }
    }

    res = requests.patch(url, json=data, headers=headers)
    return res  