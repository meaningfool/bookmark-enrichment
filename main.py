import os
from flask import Flask, jsonify
from flask_httpauth import HTTPBasicAuth
import logging

DEV_MODE = "PROD"
import notion_io, enrich


#logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

app = Flask(__name__)
auth = HTTPBasicAuth()
nb_bookmark_processed_per_run = 10

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

  # Initialize bookmark categories
  twitter_bookmarks = []
  linkedin_bookmarks = []
  youtube_bookmarks = []
  other_bookmarks = []

  enriched_bookmarks = []

  # Categorize bookmarks
  for bkmk in bookmarks:
      domain = bkmk.get("domain")
      logging.debug(f"New bookmark: {bkmk['url']}")
      if domain in ["twitter.com", "x.com"]:
          logging.debug("  Twitter")
          twitter_bookmarks.append(bkmk)
      elif domain in ["linkedin.com", "www.linkedin.com"]:
          logging.debug("  LinkedIn")
          linkedin_bookmarks.append(bkmk)
      elif domain in ["youtube.com", "www.youtube.com"]:
          logging.debug("  Youtube")
          youtube_bookmarks.append(bkmk)
      elif domain is not None:
          logging.debug("  Entered the Other bookmarks")
          other_bookmarks.append(bkmk)

  # Enrich Twitter bookmarks (uncomment and adjust as needed)
  enriched_bookmarks += enrich.enrich_twitter_bookmarks(twitter_bookmarks)

  # Enrich LinkedIn bookmarks
  enriched_bookmarks += enrich.enrich_linkedin_bookmarks(linkedin_bookmarks)

  # Enrich Youtube bookmarks
  enriched_bookmarks += enrich.enrich_youtube_bookmarks(youtube_bookmarks)

  # Enrich Other bookmarks
  enriched_bookmarks += enrich.enrich_other_bookmarks(other_bookmarks)
  
  logging.debug("----  Finished enriching --------")
  # Update bookmarks in notion_io (uncomment and adjust as needed)
  [notion_io.update_bookmark_in_notion(bkmk) for bkmk in enriched_bookmarks]

  # Return bookmarks as JSON
  return jsonify(enriched_bookmarks)


@app.errorhandler(Exception)
def handle_exception(e):
  error_name = type(e).__name__
  error_message = f"{error_name}: {str(e)}"
  
  # Log the error and return a generic error response
  app.logger.error(f"An error occurred: {error_message}")
  return jsonify({"message": f"An error occurred: {error_message}"}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=False)
