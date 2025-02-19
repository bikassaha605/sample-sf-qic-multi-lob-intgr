import json
import os
import boto3
from botocore.exceptions import ClientError
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
connect_client = boto3.client('connect')
qconnect_client = boto3.client('qconnect')

def lambda_handler(event, context):
    """
    Lambda function to select appropriate Q AI Agent based on contact attributes
    and update the Wisdom session.
    """
    # Define the expected Response Data for the Amazon Connect Contact Flow
    response_data = {
        "statusCode": 200,
        "body": "",
        "session_arn": "",
        "assistant_id": "",
        "session_id": "",
        "session_info": ""
    }

    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Retrieve contact data from the Connect Contact Event
        contact_data = event.get('Details', {}).get('ContactData')
        logger.info(f"Contact Data: {json.dumps(contact_data)}")

        # Step 1: Describe the current Amazon Connect Contact - Retrieve QIC Session Information
        try:
            contact_response = connect_client.describe_contact(
                InstanceId=contact_data.get('InstanceARN'),
                ContactId=contact_data.get('ContactId')
            ).get("Contact")
            
            logger.info(f"Describe ContactId {contact_data.get('ContactId')}: {json.dumps(contact_response, default=str)}")
        except ClientError as e:
            error_message = f"ClientError - DescribeContact for ContactId: {contact_data.get('ContactId')} - {e}"
            logger.error(error_message)
            response_data.update({
                "statusCode": 500,
                "body": error_message
            })
            return response_data

        # Step 2: Extract and parse the QConnect Session ARN
        session_arn = contact_response.get("WisdomInfo", {}).get("SessionArn")
        assistant_id, session_id = session_arn.split('/')[1], session_arn.split('/')[2]
        response_data.update({
            "session_arn": session_arn,
            "assistant_id": assistant_id,
            "session_id": session_id
        })

        # Get contact attributes
        attributes = contact_data.get("Attributes", {}) #event.get('Details', {}).get('Parameters', {})
        lob = attributes.get('LOB', '').upper()

        # Validate required parameters
        if not lob:
            raise ValueError("Missing LOB parameter")
        if not session_id:
            raise ValueError("Missing SessionId parameter")
        if not assistant_id:
            raise ValueError("Missing AssistantId parameter")
            
        # Get AI Agent IDs based on LOB
        answer_rec_agent_id = os.environ.get(f'ANSWER_REC_AGENT_ID_{lob}')
        manual_search_agent_id = os.environ.get(f'MANUAL_SEARCH_AGENT_ID_{lob}')
        
        if not answer_rec_agent_id:
            error_message = f"No Answer Recommendation Agent ID configured for LOB: {lob}"
            logger.error(error_message)
            raise ValueError(error_message)
            
        if not manual_search_agent_id:
            error_message = f"No Manual Search Agent ID configured for LOB: {lob}"
            logger.error(error_message)
            raise ValueError(error_message)
            
        logger.info(f"Selected Answer Recommendation Agent ID {answer_rec_agent_id} and Manual Search Agent ID {manual_search_agent_id} for LOB {lob}")
        
        # Update Wisdom session with both AI Agent IDs
        update_response = qconnect_client.update_session(
            assistantId=assistant_id,
            sessionId=session_id,
            description="Updated session with AI agent configuration",
            aiAgentConfiguration={
                "MANUAL_SEARCH": {
                    "aiAgentId": manual_search_agent_id
                },
                "ANSWER_RECOMMENDATION": {
                    "aiAgentId": answer_rec_agent_id
                }
            }
        )
        
        logger.info(f"Successfully updated session: {json.dumps(update_response)}")
        
        response_data.update({
            "body": {
                "AnswerRecommendationAgentId": answer_rec_agent_id,
                "ManualSearchAgentId": manual_search_agent_id,
                "LOB": lob
            },
            "session_info": update_response
        })
        
        return response_data
        
    except Exception as e:
        error_message = f"Error processing request: {str(e)}"
        logger.error(error_message)
        response_data.update({
            "statusCode": 500,
            "body": {
                "error": error_message
            }
        })
        return response_data
