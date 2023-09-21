import os
from flask import Flask, jsonify
from flask_httpauth import HTTPBasicAuth
import notion_io
import utils
from urllib.parse import urlparse
import logging

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

app = Flask(__name__)
auth = HTTPBasicAuth()
nb_bookmark_processed_per_run = 1

USER_NAME = os.environ['USER_NAME']
PASSWORD = os.environ['PASSWORD']

@auth.verify_password
def verify_password(username, password):
    if username == USER_NAME and password == PASSWORD:
        return username

@app.route('/')
def home():
    return "Hello, world!"

@app.route('/api/process_new_bookmarks', methods=['POST'])
@auth.login_required
def process_new_bookmarks():

  # Retrieve bookmarks
  unprocessed_bookmarks_list = notion_io.get_unprocessed_bookmarks()[-nb_bookmark_processed_per_run:]

  for bookmark in unprocessed_bookmarks_list:
    notion_page_id = bookmark['id']
    bookmarked_url = bookmark['properties']['URL']['url']
    parsed_url = urlparse(bookmarked_url)
    logging.debug("Bookmark URL about to be processed: %s", bookmarked_url)

    if (parsed_url.netloc in ['twitter.com', 'www.twitter.com']):
      # Retrieve de tweet content
      tweet_id = parsed_url.path.split('/')[-1]
      (tweet_text, tweet_author) = utils.parse_tweet_content(tweet_id)

      # Create a good title
      logging.debug("Twitter: reached generate title")
      bookmark_title = utils.generate_tweet_title(tweet_text)

      # Update Notion
      logging.debug("Twitter: reached notion update")
      notion_io.update_properties(notion_page_id, bookmark_title, tweet_author)
      notion_io.append_tweet_embed_to_page(notion_page_id, bookmarked_url)
      notion_io.update_status(notion_page_id)

    elif (parsed_url.netloc != ''):
      # Create the article data
      title, author, summary = utils.get_article_data(bookmarked_url)
      
      # Update Notion page
      logging.debug("NOT twitter: reached notion update")
      notion_io.update_properties(notion_page_id, title, author)
      notion_io.append_text_to_page(notion_page_id, summary)
      notion_io.update_status(notion_page_id)
  
  return jsonify({"message":"Success"}), 200


@app.errorhandler(Exception)
def handle_exception(e):
  error_name = type(e).__name__
  error_message = f"{error_name}: {str(e)}"
  
  # Log the error and return a generic error response
  app.logger.error(f"An error occurred: {error_message}")
  return jsonify({"message": f"An error occurred: {error_message}"}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=False)
