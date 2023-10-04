import requests
import json
import os
from urllib.parse import urlparse
import logging

# Replace these with your API Key and Database ID
NOTION_API_KEY = os.environ['NOTION_API_KEY']
#NOTION_DATABASE_ID = os.environ['NOTION_DATABASE_ID'] #Prod DB
NOTION_DATABASE_ID = os.environ['NOTION_DEV_DATABASE_ID'] #Dev DB

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
  print(json.dumps(data))
  response = requests.post(url, headers=headers, data=json.dumps(data))
  print(response.status_code, response.reason)

  ## Raise an error if the bookmarks cannot be retrieved
  if response.status_code != 200:
    custom_message = "Failed to retrieve Notion bookmarks"
    raise requests.HTTPError(f'{response.status_code}: {response.reason}. {custom_message}', response=response)

  return response.json()['results']

def create_bookmarks_dict(notion_raw_bookmarks):
    bookmarks = []
    for item in notion_raw_bookmarks:
        bookmark = {
            "notion_id": item['id'],
            "url": item['properties']['URL']['url'],
            "domain": urlparse(item['properties']['URL']['url']).netloc
        }
        bookmarks.append(bookmark)
    return bookmarks


def update_bookmark_in_notion(bookmark):

  bookmark["image_url"] = "https://pbs.twimg.com/media/F3ACTu9bwAABtq0?format=jpg&name=900x900"
  bookmark["summary"] = '''Voici un petit résumé
  
  avec un passage à la ligne
  
  et un second'''

  res1 = update_properties(bookmark)
  res2 = update_children(bookmark)
  
  return res1, res2

def update_properties(bookmark):
  url = f"https://api.notion.com/v1/pages/{bookmark['notion_id']}"
  data = {
    "properties": {
        "Name": {
            "title": [
                {
                    "type": "text", 
                    "text": { 
                        "content": bookmark["title"]
                    }
                }
            ]
        },
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
  }
  
  res = requests.patch(url, json=data, headers=headers)
  return res

def update_children(bookmark):

  url = f"https://api.notion.com/v1/blocks/{bookmark['notion_id']}/children"
  children = []
  
  if bookmark.get("image_url"):
    child = {
      "object": "block",
      "type": "image",
      "image": {
        "type": "external",
        "external": {
          "url": bookmark.get("image_url") 
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

  logging.debug(f"children data: {data}")
  res = requests.patch(url, json=data, headers=headers)
  logging.debug(f"children response: {res.text}")
  return res
    

'''
def append_tweet_embed_to_page(page_id, tweet_url):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"

    data = {
        "children": [
            {
                "object": "block",
                "type": "embed",
                "embed": {
                    "url": tweet_url
                }
            },
        ],
    }

    res = requests.patch(url, json=data, headers=headers)
    
    return res

def append_text_to_page(page_id, text):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"

    data = {
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
            						"type": "text",
            						"text": {
            							"content": text,
            							"link": None
            						    }
            					  }
                    ]
                }
            },
        ],
    }

    res = requests.patch(url, json=data, headers=headers)
    print(res.content)
    
    return res

def update_status(page_id):
    url = f"https://api.notion.com/v1/pages/{page_id}"

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
'''