import os
from flask import Flask, jsonify
from flask_httpauth import HTTPBasicAuth
import notion_io
import utils
from urllib.parse import urlparse

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
    try:
      unprocessed_bookmarks_list = notion_io.get_unprocessed_bookmarks()[-nb_bookmark_processed_per_run:]

      for bookmark in unprocessed_bookmarks_list:
        notion_page_id = bookmark['id']
        bookmarked_url = bookmark['properties']['URL']['url']
        parsed_url = urlparse(bookmarked_url)

        if (parsed_url.netloc in ['twitter.com', 'www.twitter.com']):
          # retrieve de tweet content
          tweet_id = parsed_url.path.split('/')[-1]
          (tweet_text, tweet_author) = utils.parse_tweet_content(tweet_id)

          # create a good title
          try:
            bookmark_title = utils.generate_tweet_title(tweet_text)
          except:
            bookmark_title = "Error generating the title"

          notion_io.update_properties(notion_page_id, bookmark_title, tweet_author)
          notion_io.append_tweet_embed_to_page(notion_page_id, bookmarked_url)
          notion_io.update_status(notion_page_id)

        elif (parsed_url.netloc != ''):

          # create the article data
          try:
            title, author, summary = utils.get_article_data(bookmarked_url)
          except:
            title = "Error with OpenAI"
            author = "Error with OpenAI"
            summary = "Error with OpenAI"
          
          # update Notion page
          notion_io.update_properties(notion_page_id, title, author)
          notion_io.append_text_to_page(notion_page_id, summary)
          notion_io.update_status(notion_page_id)
      
      return jsonify({"message":"Success"}), 200

    except Exception as e:
        return jsonify({"message": "An error occurred: {}".format(str(e))}), 500




if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
