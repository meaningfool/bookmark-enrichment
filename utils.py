import requests
import json
import boto3
import botocore.auth
import botocore.awsrequest
import logging
import datetime

from main import DEV_MODE

def get_image_url(url):
  if url.startswith("s3://"):
    return convert_s3_to_http_url(url)
  elif not url.lower().endswith(('.jpg', '.png')):
    return download_and_upload_to_s3(url)
  else:
    return url

def convert_s3_to_http_url(s3_url):
    # Split the S3 URL into bucket and key
    parts = s3_url.replace("s3://", "").split("/")
    bucket = parts[0]
    key = "/".join(parts[1:])
    
    # Construct and return the HTTP URL
    http_url = f"http://{bucket}.s3.amazonaws.com/{key}"
    return http_url

def download_and_upload_to_s3(image_url):
    """
    Download image from a URL and upload it to Amazon S3 bucket.

    Parameters:
    image_url (str): URL of the image to be downloaded and uploaded.
    bucket_name (str): Name of the S3 bucket.
    s3_file_name (str): Desired file name to be used in S3.
    """
    # Initialize boto3 S3 client
    s3 = boto3.client('s3')

    # Get the current timestamp and convert it to a string
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    
    bucket_name = "bookmark-scrapper-bucket"
    s3_file_name = f"{DEV_MODE.lower()}/uploaded_image_{timestamp}.jpg"
    logging.debug(f"download and upload, url: {image_url}")

    try:
        # Get image from URL
        response = requests.get(image_url, stream=True)
        response.raise_for_status()

        # Ensure the image is treated as binary data
        response.raw.decode_content = True

        # Upload image to S3
        s3.upload_fileobj(response.raw, bucket_name, s3_file_name)
        print(f"Successfully uploaded {s3_file_name} to {bucket_name}")

        public_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_file_name}"
        return public_url

    except requests.exceptions.RequestException as e:
        print(f"Error getting image from URL: {e}")

    except Exception as e:
        print(f"An error occurred: {e}")