# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

#import logging
import sys
import os
from logger import get_logger
from s3_manager import S3Manager
import boto3

logger = get_logger(__name__)    

def lambda_handler(event, context):
    """
    AWS Lambda handler function for processing S3 objects.
    
    Args:
        event (dict): The event dict containing the triggering event
        context: The Lambda context object
        
    Returns:
        dict: Response from the controller
    """
    REQUIRED_ENV_VARS = frozenset({
        'LOB_MAPPING'
    })
    
    DEFAULT_CONFIG = {
        "BATCH_SIZE": int(os.environ.get('BATCH_SIZE', '25')),
        "MAX_THREADS": int(os.environ.get('MAX_THREADS', '10'))
    }

    try:
        # Validate all required environment variables exist
        missing_vars = REQUIRED_ENV_VARS - set(os.environ.keys())
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        # Build config using dictionary comprehension
        config = {
            **DEFAULT_CONFIG,
            **{key: os.environ[key] for key in REQUIRED_ENV_VARS}
        }

        return S3Manager(config).controller(event)

    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Failed to process S3 objects: {str(e)}")
        raise

                                                                                                       
if __name__ == "__main__":
    lambda_handler({}, None)
