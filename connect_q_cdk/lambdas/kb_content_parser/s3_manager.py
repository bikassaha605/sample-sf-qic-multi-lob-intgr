#import logging
import boto3
import json
import os
from typing import Dict, List, Tuple
from botocore.exceptions import ClientError
from botocore.config import Config
from html_sanitizer import HTMLSanitizer
import concurrent.futures
from logger import get_logger
from urllib.parse import unquote_plus

# Configure logging
logger = get_logger(__name__)  

# Configure boto3 with retries and timeouts
boto3_config = Config(
    retries=dict(
        max_attempts=3
    ),
    connect_timeout=5,
    read_timeout=60,
    parameter_validation=True
)

class S3Manager:
    def __init__(self, config):
        self.s3_client = boto3.client('s3', config=boto3_config)
        self.config = config
        self.sanitizer = HTMLSanitizer()
        self.content_field = os.environ.get('CONTENT_FIELD', 'Content__c')
    
    def list_s3_objects(self, bucket: str, prefix: str = '') -> List[str]:
        """
        Lists all objects in the specified S3 bucket and prefix
        """
        try:
            objects = []
            paginator = self.s3_client.get_paginator('list_objects_v2')
            
            for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                if 'Contents' in page:
                    objects.extend([obj['Key'] for obj in page['Contents']])
            
            logger.info(f"Found {len(objects)} objects in {bucket}/{prefix}")
            return objects
            
        except ClientError as e:
            logger.error(f"Error listing objects in bucket {bucket}: {str(e)}")
            raise
    
    def read_s3_object(self, bucket: str, s3_key: str) -> List[Dict]:
        """
        Reads a JSON object from S3 and returns its contents.

        Args:
            bucket (str): The name of the S3 bucket.
            key (str): The key of the S3 object.

        Returns:
            List[Dict]: A list of dictionaries representing the JSON objects read from the S3 object.
        """
        try:
            logger.info(f"Reading object {s3_key} from bucket {bucket}")
            try:
                response = self.s3_client.get_object(Bucket=bucket, Key=s3_key)
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    logger.error(f"Object {s3_key} not found in bucket {bucket}")
                    return []
                raise
            
            articles = []
            # Use streaming to process the file in chunks
            for line in response['Body']._raw_stream:
                line = line.decode('utf-8').strip()
                if not line:
                    continue
                    
                try:
                    article = json.loads(line)
                    if not self.validate_article(article):
                        continue
                    
                    # Process valid articles with dict comprehension
                    sanitized_article = {
                        **article,
                        'Title': self.sanitizer.sanitize_html(article['Title']),
                        self.content_field: self.sanitizer.sanitize_html(article[self.content_field])
                    }
                    articles.append(sanitized_article)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON line: {line[:100]}... Error: {str(e)}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing line: {str(e)}")
                    continue
            
            logger.info(f"Successfully read {len(articles)} records from {s3_key}")
            return articles
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"Error reading S3 object {s3_key}: {error_code} - {str(e)}")
            raise

    def validate_article(self, article: Dict) -> bool:
        """
        Validate required fields in the article
        Args:
            article: The article data to validate
        Returns:
            bool: True if article is valid, False otherwise
        """
        REQUIRED_FIELDS = frozenset({"Id", "Title", "ArticleNumber", self.content_field})
        
        if not isinstance(article, dict):
            logger.error("Article data must be a dictionary")
            return False

        missing_fields = {field for field in REQUIRED_FIELDS if not article.get(field)}
        if missing_fields:
            logger.error(f"Invalid or missing required fields: {', '.join(missing_fields)}")
            return False
        
        return True

    def save_html_batch(self, html_files: List[Tuple[str, str, str, str]]) -> List[bool]:
        """
        Saves multiple HTML files to S3 in batch.

        Args:
            html_files (List[Tuple[str, str, str, str]]): A list of tuples where each tuple contains:
                - content (str): The HTML content to save.
                - title (str): The title of the HTML file.
                - bucket (str): The name of the S3 bucket to save the file in.
                - prefix (str): The prefix to use for the S3 key.

        Returns:
            List[bool]: A list of boolean values indicating the success (True) or failure (False) of each save operation.
        """
        if not html_files:
            return []

        # Define common parameters
        common_params = {
            'ContentType': 'text/html',
            'CacheControl': 'max-age=3600'
        }

        # Use ThreadPoolExecutor for parallel uploads
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config['MAX_THREADS']) as executor:
            def upload_file(file_tuple):
                content, title, urlName, bucket, prefix = file_tuple
                try:
                    key = f"{prefix}{urlName}.html"
                    try:
                        self.s3_client.put_object(
                            Bucket=bucket,
                            Key=key,
                            Body=content,
                            **common_params
                        )
                    except ClientError as e:
                        logger.error(f"Failed to upload {key}: {e.response['Error']['Message']}")
                        return False
                    logger.debug(f"Successfully saved HTML file: {key}")
                    return True
                except Exception as e:
                    logger.error(f"Error saving HTML file for {title}: {str(e)}")
                    return False

            # Execute uploads in parallel and collect results
            results = list(executor.map(upload_file, html_files))

        return results
    
    def delete_html_batch(self, files_to_delete: List[Tuple[str, str, str]]) -> List[bool]:
        """
        Deletes multiple HTML files from S3 in batch.

        Args:
            files_to_delete (List[Tuple[str, str, str]]): A list of tuples where each tuple contains:
                - title (str): The title of the HTML file.
                - bucket (str): The name of the S3 bucket to delete the file from.
                - prefix (str): The prefix used in the S3 key.

        Returns:
            List[bool]: A list of boolean values indicating the success (True) or failure (False) of each delete operation.
        """
        if not files_to_delete:
            return []

        # Use ThreadPoolExecutor for parallel deletions
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config['MAX_THREADS']) as executor:
            def delete_file(file_tuple):
                title, urlName, bucket, prefix = file_tuple
                try:
                    key = f"{prefix}{urlName}.html"
                    try:
                        self.s3_client.delete_object(
                            Bucket=bucket,
                            Key=key
                        )
                    except ClientError as e:
                        logger.error(f"Failed to delete {key}: {e.response['Error']['Message']}")
                        return False
                    logger.debug(f"Successfully deleted HTML file: {key}")
                    return True
                except Exception as e:
                    logger.error(f"Error deleting HTML file for {title}: {str(e)}")
                    return False

            # Execute deletions in parallel and collect results
            results = list(executor.map(delete_file, files_to_delete))

        return results  
    
    def get_lob_bucket_mapping(self) -> Dict[str, str]:
        """
        Parse the LOB_MAPPING environment variable to create a mapping of LOB prefixes to bucket names.
        
        Returns:
            Dict[str, str]: A dictionary mapping LOB prefixes to their corresponding bucket names
        """
        mapping = {}
        lob_mapping_str = self.config.get('LOB_MAPPING', '')
        
        for mapping_pair in lob_mapping_str.split(','):
            if ':' in mapping_pair:
                prefix, bucket = mapping_pair.strip().split(':')
                mapping[prefix] = bucket
                
        return mapping

    def process_batch(self, records: List[Dict], lob_prefix: str) -> List[bool]:
        """
        Process a batch of records and save them as HTML files to S3.

        Args:
            records (List[Dict]): A list of dictionaries representing the records to process.
            lob_prefix (str): The LOB prefix to determine the output bucket.

        Returns:
            List[bool]: A list of boolean values indicating the success or failure of saving each HTML file.
        """
        if not records:
            return []

        try:
            # Get the output bucket for this LOB
            lob_bucket_mapping = self.get_lob_bucket_mapping()
            if lob_prefix not in lob_bucket_mapping:
                logger.error(f"No output bucket mapping found for LOB prefix: {lob_prefix}")
                return [False] * len(records)
                
            output_bucket = lob_bucket_mapping[lob_prefix]
            output_prefix = ""  # We don't need a prefix since we're using dedicated buckets

            # Use list comprehension instead of append in a loop
            files_to_save = [
                (record.get(self.content_field), record.get("Title"), record.get("UrlName"), output_bucket, output_prefix)
                for record in records
                if record.get(self.content_field) and record.get("Title") and record.get("UrlName")
                and record.get("PublishStatus") == "Online"                
            ]

            files_to_delete = [
                (record.get("Title"), record.get("UrlName"), output_bucket, output_prefix)
                for record in records
                if record.get("Title") and record.get("UrlName") 
                and record.get("PublishStatus") == "Archived"
            ]

            results = []

            # Process files to save
            if files_to_save:
                save_results = self.save_html_batch(files_to_save)
                results.extend(save_results)

            # Process files to delete
            if files_to_delete:
                delete_results = self.delete_html_batch(files_to_delete)
                results.extend(delete_results)

            # If no files were processed, return False for each record
            return results if results else [False] * len(records)
        
        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")
            return [False] * len(records)

    
    def process_s3_object(self, bucket: str, s3_key: str) -> Tuple[int, int]:
        """
        Process a single S3 object and return success/failure counts.

        Args:
            bucket (str): The name of the S3 bucket.
            s3_key (str): The key of the S3 object.

        Returns:
            Tuple[int, int]: A tuple containing the count of successfully processed records and the count of failed records.
        """
        try:
            # Extract LOB prefix from the S3 key
            key_parts = s3_key.split('/')
            if not key_parts:
                logger.error(f"Invalid S3 key format: {s3_key}")
                return 0, 0
                
            lob_prefix = key_parts[0]  # The first part of the key should be the LOB prefix
            
            json_records = self.read_s3_object(bucket, s3_key)
            
            # Create generator for batches instead of list comprehension
            def batch_generator():
                for i in range(0, len(json_records), self.config['BATCH_SIZE']):
                    yield json_records[i:i + self.config['BATCH_SIZE']]
            
            successful = failed = 0
            
            # Process batches using thread pool
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.config['MAX_THREADS']) as executor:
                futures = [
                    executor.submit(self.process_batch, batch, lob_prefix)
                    for batch in batch_generator()
                ]
                
                # Process results as they complete
                for future in concurrent.futures.as_completed(futures):
                    batch_result = future.result()
                    successful += sum(batch_result)
                    failed += len(batch_result) - sum(batch_result)
            
            return successful, failed
            
        except Exception as e:
            logger.error(f"Error processing object {s3_key}: {str(e)}")  # Fixed variable name
            return 0, 0

    def controller(self, event):   
        """
        Processes an S3 event triggered by an SQS message.

        Args:
            event (dict): A dictionary containing SQS messages with S3 event details.

        Returns:
            dict: A dictionary containing the status code and a message with the count of successful and failed records processed.
        """        
        def create_response(status_code, message, successful=0, failed=0):
            return {
                'statusCode': status_code,
                'body': json.dumps({
                    'message': message,
                    'successful': successful,
                    'failed': failed
                })
            }

        try:           
            if not event.get('Records'):
                return create_response(204, 'No Content')
            
            total_successful = total_failed = 0
            
            # Process S3 events
            for record in event['Records']:
                try:
                    sqs_message_body = json.loads(record['body'])
                    s3_records = sqs_message_body.get('Records', [])
                    
                    if not s3_records or 's3' not in s3_records[0]:
                        logger.error("Invalid S3 event structure in SQS message")
                        continue

                    s3_event = s3_records[0]['s3']
                    bucket = s3_event['bucket']['name']
                    key = unquote_plus(s3_event['object']['key'])
                    
                    logger.info(f"Processing S3 object - bucket: {bucket}, key: {key}")
                    successful, failed = self.process_s3_object(bucket, key)
                    total_successful += successful
                    total_failed += failed

                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Error processing record: {str(e)}")
                    continue
            
            logger.info(f"Processing complete. Total Successful: {total_successful}, Total Failed: {total_failed}")
            return create_response(200, 'Processing complete', total_successful, total_failed)
                
        except Exception as e:
            logger.error(f"Fatal error in controller: {str(e)}")
            return create_response(500, 'Internal server error')
