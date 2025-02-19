import os
import boto3
import json
import time

def handler(event, context):
    try:
        # Get assistant ARN and validate
        assistant_arn = os.environ.get('ASSISTANT_ARN')
        if not assistant_arn:
            raise ValueError("ASSISTANT_ARN environment variable is required")
        if not assistant_arn.startswith('arn:aws:wisdom'):
            raise ValueError("Invalid ASSISTANT_ARN format")

        # Create CloudWatch Logs client
        logs = boto3.client('logs')
        
        # Get region and account ID from Lambda context
        region = context.invoked_function_arn.split(':')[3]
        account_id = context.invoked_function_arn.split(':')[4]
        
        # Log group name for Amazon Q logs
        log_group_name = f"/aws/connect/amazon-q/{assistant_arn.split('/')[-1]}"
        
        # First, ensure the log group exists
        try:
            logs.create_log_group(logGroupName=log_group_name)
            print(f"Created new log group: {log_group_name}")
        except logs.exceptions.ResourceAlreadyExistsException:
            print(f"Log group already exists: {log_group_name}")
        
        # Generate consistent names using assistant ID
        source_name = f"amazon-q-logging-delivery-source"
        destination_name = f"amazon-q-logging-delivery-destination"

        # 1. Create delivery source
        delivery_source_response = logs.put_delivery_source(
            logType='EVENT_LOGS',
            name=source_name,
            resourceArn=assistant_arn
        )
        print(f"Delivery source response: {json.dumps(delivery_source_response)}")
        source_name = delivery_source_response.get('deliverySource', {}).get('name')
        if not source_name:
            raise ValueError(f"Failed to get source name from response: {delivery_source_response}")

        # 2. Create delivery destination
        delivery_destination_response = logs.put_delivery_destination(
            deliveryDestinationConfiguration={
                'destinationResourceArn': f"arn:aws:logs:{region}:{account_id}:log-group:{log_group_name}:*"
            },
            name=destination_name,
            outputFormat='json'
        )
        
        print(f"Delivery destination response: {json.dumps(delivery_destination_response)}")
        
        # Get the ARN from the response
        destination_arn = delivery_destination_response.get('deliveryDestination', {}).get('arn')
        if not destination_arn:
            raise ValueError(f"Failed to get destination ARN from response: {delivery_destination_response}")

        # Add a small delay to ensure the destination is fully created
        time.sleep(2)

        # 3. Link source to destination
        create_delivery_response = logs.create_delivery(
            deliveryDestinationArn=destination_arn,
            deliverySourceName=source_name
        )
        
        print(f"Create delivery response: {json.dumps(create_delivery_response)}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully configured Amazon Q logging',
                'log_group': log_group_name,
                'source_name': source_name,
                'destination_name': destination_name
            })
        }
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Error configuring Amazon Q logging',
                'error': str(e)
            })
        }
