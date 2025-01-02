import json
import os
import boto3
from datetime import datetime
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import urllib3

# AWS region and OpenSearch configuration
region = 'us-east-1'
service = 'es'
opensearch_host = 'https://search-photos-vwq2mc5smim4i4b6brp5plt7xe.us-east-1.es.amazonaws.com'  # Replace with your OpenSearch endpoint

# AWS Clients
rekognition = boto3.client('rekognition', region_name=region)
s3 = boto3.client('s3')

# Initialize HTTP connection pool
http = urllib3.PoolManager()

# Credentials for signing requests
credentials = boto3.Session().get_credentials()

def lambda_handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Requested-With,x-amz-meta-customlabels',
        'Access-Control-Allow-Methods': 'PUT,OPTIONS',  
        'Access-Control-Allow-Credentials': 'true',
        'Access-Control-Expose-Headers': 'Content-Length,Content-Type'  
    }
    
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:        
        # Process the S3 PUT event
        for record in event['Records']:
            bucket_name = record['s3']['bucket']['name']
            object_key = record['s3']['object']['key']

            valid_extensions = ['.jpg', '.jpeg', '.png']
            if not os.path.splitext(object_key)[-1].lower() in valid_extensions:
                print(f"File {object_key} is not a valid image. Skipping Rekognition.")
                return {
                    'statusCode': 500,
                    'body': json.dumps('An error occurred.')
                }
            
            # Detect labels using Rekognition
            rekognition_response = rekognition.detect_labels(
                Image={'S3Object': {'Bucket': bucket_name, 'Name': object_key}},
                MaxLabels=10
            )
            detected_labels = [label['Name'] for label in rekognition_response['Labels']]
            
            # Retrieve custom metadata from S3 object
            s3_metadata = s3.head_object(Bucket=bucket_name, Key=object_key)
            custom_labels = s3_metadata['Metadata'].get('customlabels', '')
            custom_labels = [label.strip() for label in custom_labels.split(',') if label.strip()]
            
            # Combine Rekognition labels and custom labels
            labels_array = list(set(detected_labels + custom_labels))
            
            # Prepare JSON object for ElasticSearch
            created_timestamp = s3_metadata['LastModified'].isoformat()  # Convert timestamp to ISO format
            photo_metadata = {
                "objectKey": object_key,
                "bucket": bucket_name,
                "createdTimestamp": created_timestamp,
                "labels": labels_array
            }
            
            # Prepare request for OpenSearch (ElasticSearch)
            endpoint = f"{opensearch_host}/photos/_doc/"
            headers = {"Content-Type": "application/json"}
            
            # Create signed request
            request = AWSRequest(method='POST', url=endpoint, headers=headers, data=json.dumps(photo_metadata))
            SigV4Auth(credentials, service, region).add_auth(request)
            
            # Send request using urllib3
            response = http.request(
                'POST',
                request.url,
                headers=dict(request.headers),
                body=request.body
            )
            
            # Log the response
            print(f"ElasticSearch Response: {response.data.decode('utf-8')}")
        
        return {
            'statusCode': 200,
            'headers': headers, 
            'body': json.dumps('Photo indexed successfully!')
        }
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,  
            'body': json.dumps('An error occurred.')
        }
