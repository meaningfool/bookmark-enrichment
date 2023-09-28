import os
from bs4 import BeautifulSoup
import requests
import json
import logging
import asyncio
from playwright.async_api import async_playwright

BRIGHTDATA_USER = os.environ['BRIGHTDATA_USER']
BRIGHTDATA_PASS = os.environ['BRIGHTDATA_PASS']

AUTH = f'{BRIGHTDATA_USER}:{BRIGHTDATA_PASS}'  # Replace with your actual Brightdata credentials
SBR_WS_CDP = f'wss://{AUTH}@brd.superproxy.io:9222'

SCREENSHOT_PATH = './screenshot.png'

async def scrape_twitter_embed(tweet_id):
  async with async_playwright() as pw:
    print('Connecting to Scraping Browser...')
    browser = await pw.chromium.connect_over_cdp(SBR_WS_CDP)
    try:
        page = await browser.new_page()
        await page.goto(f'https://platform.twitter.com/embed/Tweet.html?id={tweet_id}', timeout=2*60*1000)
        
        # Wait for a selector that indicates the tweet content has loaded
        await page.wait_for_selector("article")
        
        # Additional delay to ensure everything loads
        await asyncio.sleep(1) 
        
        # Take screenshot of the specific element
        element = await page.query_selector("article")
        screenshot_path = './screenshot.png'
        print(f'Taking element screenshot to file {screenshot_path}')
        await element.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        print('Navigated! Scraping page content...')
        html_content = await page.content()
        return html_content 
    finally:
        await browser.close()


def extract_tweet_info(data):
  # Convert HTML response to JSON
  soup = BeautifulSoup(response.content, 'html.parser')
  return json.loads(soup.text)

  # Extract tweet text and author from JSON data.
  tweet_text = data.get("text")
  tweet_author = data.get("user", {}).get("name")

  if not tweet_text or not tweet_author:
      logging.error("Expected keys not found in Tweet payload")
      raise ValueError("Expected keys not found in Tweet payload")

  return tweet_text, tweet_author


def parse_tweet_content(tweet_id):
  # Main function to parse tweet content given a tweet ID.
  html = asyncio.run(scrape_twitter_embed(tweet_id))
  return extract_tweet_info(data)
