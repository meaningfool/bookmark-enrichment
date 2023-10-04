import requests
import json
import boto3
import botocore.auth
import botocore.awsrequest

def sign_aws_lambda_request(url, method, headers, body, service, region):
    session = boto3.Session()
    credentials = session.get_credentials()

    # Create an AWSRequest object
    request = botocore.awsrequest.AWSRequest(method=method, url=url, headers=headers, data=body)

    # Create a SigV4 signer
    signer = botocore.auth.SigV4Auth(credentials, service, region)

    # Sign the request
    signer.add_auth(request)

    # Get the signed headers
    signed_headers = request.headers

    return signed_headers


def prepare_aws_lambda_request(body):
    url = 'https://liem3isss5jhitalsclmhrpcxi0igcdl.lambda-url.eu-west-3.on.aws/'
    method = 'POST'
    headers = {'Content-Type': 'application/json'}
    body = body
    service = 'lambda'
    region = 'eu-west-3'

    signed_headers = sign_aws_lambda_request(url, method, headers, body, service, region)
    req = requests.Request(method, url, headers=signed_headers, data=body)
    return req.prepare()