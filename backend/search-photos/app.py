# import json
# import boto3
# from botocore.auth import SigV4Auth
# from botocore.awsrequest import AWSRequest
# import urllib3

# # AWS and OpenSearch Configuration
# region = 'us-east-1'
# service = 'es'
# opensearch_host = 'https://search-photos-vwq2mc5smim4i4b6brp5plt7xe.us-east-1.es.amazonaws.com'  # Replace with your OpenSearch endpoint

# # AWS Clients
# lex_client = boto3.client('lexv2-runtime')
# http = urllib3.PoolManager()
# credentials = boto3.Session().get_credentials()

# def lambda_handler(event, context):
#     try:
#         if not event:
#             return {
#                 'statusCode': 400,
#                 'headers': {'Content-Type': 'application/json'},
#                 'body': json.dumps({'message': 'Event data is missing.'})
#             }
        
#         # Step 1: Extract search query 'q' from the query string parameters
#         query = event.get('queryStringParameters', {}).get('q', '')
#         if not query:
#             return {
#                 'statusCode': 400,
#                 'headers': {'Content-Type': 'application/json'},
#                 'body': json.dumps({'message': 'Missing search query parameter.'})
#             }
        
#         # Step 2: Disambiguate query using Amazon Lex
#         lex_response = lex_client.recognize_text(
#             botId='IXSFYWNUGC',  # Replace with your Lex bot ID
#             botAliasId='TSTALIASID',  # Replace with your bot alias ID
#             localeId='en_US',
#             sessionId='testsession',
#             text=query
#         )

#         print("Lex response: ", lex_response)
        
#         # Extract slots or interpretations from the Lex response
#         slots = lex_response.get('interpretations', [])[0].get('intent', {}).get('slots', {})
#         keywords = [slot['value']['interpretedValue'] for slot in slots.values() if slot and 'value' in slot]

#         print("Extracted slots: ", slots)

#         # If no keywords were found, return an empty result array
#         if not keywords:
#             return {
#                 'statusCode': 200,
#                 'headers': {'Content-Type': 'application/json'},
#                 'body': json.dumps([])
#             }
        
#         # Step 3: Search the OpenSearch index
#         search_query = {
#             "query": {
#                 "bool": {
#                     "should": [{"match": {"labels": keyword}} for keyword in keywords]
#                 }
#             }
#         }

#         # Prepare signed request to OpenSearch
#         endpoint = f"{opensearch_host}/photos/_search"
#         headers = {"Content-Type": "application/json"}
#         request = AWSRequest(method='POST', url=endpoint, headers=headers, data=json.dumps(search_query))
#         SigV4Auth(credentials, service, region).add_auth(request)

#         # Send request using urllib3
#         response = http.request(
#             'POST',
#             request.url,
#             headers=dict(request.headers),
#             body=request.body
#         )
        
#         # Parse OpenSearch response
#         search_results = json.loads(response.data.decode('utf-8'))
#         hits = search_results.get('hits', {}).get('hits', [])

#         # Format the search results as per the API spec
#         results = [{
#             "objectKey": hit["_source"].get("objectKey"),
#             "bucket": hit["_source"].get("bucket"),
#             "labels": hit["_source"].get("labels", [])
#         } for hit in hits]
        
#         return {
#             'statusCode': 200,
#             'headers': {'Content-Type': 'application/json'},
#             'body': json.dumps(results)
#         }

#     except Exception as e:
#         print(f"Error: {str(e)}")
#         return {
#             'statusCode': 500,
#             'headers': {'Content-Type': 'application/json'},
#             'body': json.dumps({'message': 'An error occurred.', 'error': str(e)})
#         }

import json
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import urllib3

# AWS and OpenSearch Configuration
region = 'us-east-1'
service = 'es'
opensearch_host = 'https://search-photos-vwq2mc5smim4i4b6brp5plt7xe.us-east-1.es.amazonaws.com'  # Replace with your OpenSearch endpoint

# AWS Clients
lex_client = boto3.client('lexv2-runtime')
http = urllib3.PoolManager()
credentials = boto3.Session().get_credentials()

# CORS headers
CORS_HEADERS = {
   'Content-Type': 'application/json',
   'Access-Control-Allow-Origin': 'http://localhost:8080',
   'Access-Control-Allow-Methods': 'GET,OPTIONS',
   'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
}

def lambda_handler(event, context):
   try:
       if not event:
           return {
               'statusCode': 400,
               'headers': CORS_HEADERS,
               'body': json.dumps({'message': 'Event data is missing.'})
           }
       
       # Step 1: Extract search query 'q' from the query string parameters
       query = event.get('queryStringParameters', {}).get('q', '')
       if not query:
           return {
               'statusCode': 400,
               'headers': CORS_HEADERS,
               'body': json.dumps({'message': 'Missing search query parameter.'})
           }
       
       # Step 2: Disambiguate query using Amazon Lex
       lex_response = lex_client.recognize_text(
           botId='IXSFYWNUGC',  # Replace with your Lex bot ID
           botAliasId='TSTALIASID',  # Replace with your bot alias ID
           localeId='en_US',
           sessionId='testsession',
           text=query
       )

       print("Lex response: ", lex_response)
       
       # Extract slots or interpretations from the Lex response
       slots = lex_response.get('interpretations', [])[0].get('intent', {}).get('slots', {})
       keywords = [slot['value']['interpretedValue'] for slot in slots.values() if slot and 'value' in slot]

       print("Extracted slots: ", slots)

       # If no keywords were found, return an empty result array
       if not keywords:
           return {
               'statusCode': 200,
               'headers': CORS_HEADERS,
               'body': json.dumps([])
           }
       
       # Step 3: Search the OpenSearch index
       search_query = {
           "query": {
               "bool": {
                   "should": [{"match": {"labels": keyword}} for keyword in keywords]
               }
           }
       }

       # Prepare signed request to OpenSearch
       endpoint = f"{opensearch_host}/photos/_search"
       headers = {"Content-Type": "application/json"}
       request = AWSRequest(method='POST', url=endpoint, headers=headers, data=json.dumps(search_query))
       SigV4Auth(credentials, service, region).add_auth(request)

       # Send request using urllib3
       response = http.request(
           'POST',
           request.url,
           headers=dict(request.headers),
           body=request.body
       )
       
       # Parse OpenSearch response
       search_results = json.loads(response.data.decode('utf-8'))
       hits = search_results.get('hits', {}).get('hits', [])

       # Format the search results as per the API spec
       results = [{
           "objectKey": hit["_source"].get("objectKey"),
           "bucket": hit["_source"].get("bucket"),
           "labels": hit["_source"].get("labels", [])
       } for hit in hits]
       
       return {
           'statusCode': 200,
           'headers': CORS_HEADERS,
           'body': json.dumps(results)
       }

   except Exception as e:
       print(f"Error: {str(e)}")
       return {
           'statusCode': 500,
           'headers': CORS_HEADERS,
           'body': json.dumps({'message': 'An error occurred.', 'error': str(e)})
       }