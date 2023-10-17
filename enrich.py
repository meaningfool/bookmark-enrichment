import os
from bs4 import BeautifulSoup
import re
import requests
import json
import logging
import aws_lambda
from urllib.parse import urlparse, urljoin
from main import DEV_MODE
from langchain.chat_models import ChatOpenAI
from openai.error import InvalidRequestError



def enrich_twitter_bookmarks(twitter_bookmarks):
  
  twitter_bookmarks = retrieve_tweets_html(twitter_bookmarks)
  logging.debug(f"Tweets retrieved")
  
  # Extract a title and author and add them to the dict
  for bkmk in twitter_bookmarks:
    bkmk["title"], bkmk["author"] = get_tweet_title_author(bkmk)
    del bkmk["html_content"]
  
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
    html = retrieve_page_html(bkmk)
    logging.debug(f"Successfully retrieved HTML for {bkmk['url']}/n Is html Null: {html is None}")
    type = article_or_website(html)
    bkmk['type'] = type
    if type == "article":
      logging.debug(f"  Enter article loop")
      bkmk['title'] = get_article_title(html)
      logging.debug(f"  Title:{bkmk['title']}")
      bkmk['author'] = get_author(html)
      logging.debug(f"  Author:{bkmk['author']}")
      bkmk['image_url'] = get_image_url(bkmk['url'], html)
      logging.debug(f"  Image:{bkmk['image_url']}")
      bkmk['summary']= get_summary(html)
      #logging.debug(f"  Summary:{bkmk['summary']}")
    else:
      logging.debug(f"  Enter the NON-article loop")
      logging.debug(f"Head tag content: {get_clean_head_tag(html)}")
      bkmk['title'] = get_website_title(html)
      logging.debug(f"  Title:{bkmk['title']}")
  return other_bookmarks


def article_or_website(html):
  soup = BeautifulSoup(html, 'html.parser')

  meta_tag = soup.find('meta', {'property': 'og:type'})
  article = soup.find('article')
  type = ""

  if meta_tag and meta_tag.has_attr('content'):
    type = meta_tag['content']
  elif article:
    type = "article"
  else:
    type = "website"

  return type
  

def get_clean_head_tag(html):
  soup = BeautifulSoup(html, 'html.parser')
  for element in soup.find_all(['script', 'style', 'link']):
    element.decompose()
  head = soup.find('head')
  return head

def get_article_content(html):
  soup = BeautifulSoup(html, 'html.parser')
  content = ''
  
  if soup.find('article'):
    content=soup.find('article')
  elif soup.find('main'):
    content=soup.find('main')
  else:
    content=soup.find('body')
    for item in soup(["header", "nav", "footer", "svg"]):
      item.decompose()

  return content
    

def get_website_title(html):
  head = get_clean_head_tag(html)
  title = get_data(head, "Return the description. Keep only the first sentence. If you can't find a description return ''")

  return title

def get_article_title(html):
  soup = BeautifulSoup(html, 'html.parser')
  title=""
  if soup.find('h1') is not None:
    title = soup.find('h1').text
  else:
    head = get_clean_head_tag(html)
    title = get_data(head, "Return the title. If you can't find a title return '?'")

  return title

def get_author(html):
  head = get_clean_head_tag(html)
  author = get_data(head, "This is an article head tag. Return the author's name if you can find it in the metadata. Otherwise return 'Not found'. Format : First name Last name.")

  if author == 'Not found':
    author = get_data(get_article_content(html), "This is an article content. Return the author's name if you can find it. Otherwise return 'Not found'. Format : First name Last name.")

  return author


def get_image_url(url, html):
  soup = BeautifulSoup(html, 'html.parser')
  figure_tag = None
  if soup.find('figure'):
    figure_tag = soup.find('figure')
  elif soup.find(class_='figure'):
    figure_tag = soup.find(class_='figure')
  
  image_src=''
  image_url=''
  
  # Check if figure_image and its src attribute are not None before proceeding
  if figure_tag is not None and figure_tag.find('img'):
    if figure_tag.find('img').has_attr('src'):
      image_src = figure_tag.find('img')['src']
    elif figure_tag.find('img').has_attr('data-src'):
      image_src = figure_tag.find('img')['data-src']
      
  # Use urljoin to ensure the URL is absolute
  if image_src != '':
    image_url = urljoin(url, image_src)

  return image_url

def get_summary(html):
  content = get_article_content(html)
  summary = get_data(content, "This is an article content. Identify the main theses, and organize them as bullet points.")
  return summary


  
def get_data(html, prompt_variable, mode="FULL", window="4K"):
    # Text of the prompt template
    prompt = f'''You are acting as an HTML parser. {prompt_variable}

    HTML:
    '''

    if mode == "FULL":
      prompt = f"{prompt}/n{html}"
    else:
      prompt = f"{prompt}/n{html.get_text()}"

    model_name="gpt-3.5-turbo"
  
    if window == "16K":
      model_name="gpt-3.5-turbo-16k"

    # LLM
    llm = ChatOpenAI(temperature=0, openai_api_key=os.environ["OPENAI_API_KEY"], model_name=model_name) 

    # Run the chain
    try:
      data = llm.predict(prompt)
      return data
    except InvalidRequestError:
      if mode == "FULL":
        return get_data(html, prompt_variable, "SIMPLIFIED")
      elif mode == "SIMPLIFIED":
        return get_data(html, prompt_variable, "SIMPLIFIED", "16K")
      else:
        return "The HTML was too long to pass to the LLM in 1 call."