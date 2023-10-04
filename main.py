import os
from flask import Flask, jsonify
from flask_httpauth import HTTPBasicAuth
import notion_io, enrich
import logging


logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

app = Flask(__name__)
auth = HTTPBasicAuth()
nb_bookmark_processed_per_run = 20

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
  bookmarks =\
  notion_io.retrieve_bookmarks_from_notion(nb_bookmark_processed_per_run)

  # Retrieve Twitter bookmarks
  twitter_bookmarks = [bkmk for bkmk in bookmarks if bkmk["domain"] in ["twitter.com", "x.com"]]

  # Enrich Twitter bookmarks
  bookmarks = enrich.enrich_twitter_bookmarks(twitter_bookmarks)

  logging.debug(f"Nb Bookmarks: {len(bookmarks)}")
  logging.debug(f"Bookmark author : {bookmarks[0]['author']}")
  logging.debug(f"Bookmark title : {bookmarks[0]['title']}")

  # Update bookmarks in notion_io
  [notion_io.update_bookmark_in_notion(bkmk) for bkmk in bookmarks]
  
  return bookmarks
  ''''
  for bookmark in unprocessed_bookmarks_list:


      # Update Notion
      logging.debug("Twitter: reached notion update")
      notion_io.update_properties(notion_page_id, bookmark_title, tweet_author)
      notion_io.append_tweet_embed_to_page(notion_page_id, bookmarked_url)
      notion_io.update_status(notion_page_id)

      
      # Update Notion page
      logging.debug("NOT twitter: reached notion update")
      notion_io.update_properties(notion_page_id, title, author)
      notion_io.append_text_to_page(notion_page_id, summary)
      notion_io.update_status(notion_page_id)
  '''
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
