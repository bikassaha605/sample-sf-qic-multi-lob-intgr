# ConnectQ CDK

This project contains the AWS CDK infrastructure for ConnectQ, including Salesforce Knowledge Base integration.

## Prerequisites

1. AWS CDK CLI installed
2. Python 3.9 or later
3. A Salesforce account with API access
4. AWS CLI configured with appropriate credentials

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Configure Environment

1. Update config/config.dev.json with your AWS environment details:
   ```json
   {
     "vpc_id": "YOUR_VPC_ID",  // Replace with your VPC ID
     "env_name": "dev",
     "account": "YOUR_AWS_ACCOUNT",
     "region": "YOUR_AWS_REGION"
   }
   ```

### 3. Create Salesforce Connection in AppFlow

Before deploying the stack, you need to manually create the Salesforce connection in AppFlow:

1. Go to the AWS Console and navigate to Amazon AppFlow
2. Click on "Create connection" in the "Connections" section
3. Choose "Salesforce" as the connector
4. For "Connection name", use the exact name specified in your config.dev.json (default: "dev-sf-connection")
5. Choose "OAuth 2.0" as the authentication method
6. Enter your Salesforce Connected App details:
   - Client ID (from your Salesforce Connected App)
   - Client Secret (from your Salesforce Connected App)
7. Click "Continue" to authorize the connection with Salesforce
   - You'll be redirected to Salesforce to log in and authorize the connection
   - After authorization, you'll be redirected back to AWS
8. Choose the appropriate data encryption settings
9. Review and create the connection

**Important Notes:**
- The connection name must match exactly what's in your config.dev.json
- Ensure the connection is successfully created before proceeding with the CDK deployment
- If you change the connection name in config.dev.json, you'll need to create a new connection with the matching name

### 4. Deploy the Stack

After completing the configuration and creating the Salesforce connection:

```bash
cdk deploy
```

## Stack Components

The stack creates the following resources:

1. AppFlow flows for Salesforce Knowledge Base integration (using manually created connection)
2. S3 buckets for raw and processed content
3. Lambda function for content processing
4. SQS queue for S3 event notifications
5. Wisdom Knowledge Base and Assistant
6. KMS key for encryption
7. Necessary IAM roles and policies

## Development

- Make changes to the stack in connect_q_cdk/stacks/connect_q_stack.py
- Use `cdk diff` to see changes before deploying
- Run `cdk deploy` to deploy changes

## Security

- All sensitive data is encrypted using KMS
- IAM roles follow the principle of least privilege
- S3 buckets are configured with secure policies

## Troubleshooting

### Connector Profile Error
If you encounter the "Connector Profile does not exist" error:
1. Verify that you've created the Salesforce connection in AppFlow before deploying the stack
2. Check that the connection name in AppFlow exactly matches the name in config.dev.json
3. If the connection exists but still getting errors, try recreating the connection in AppFlow

## Contributing

1. Create a feature branch
2. Make your changes
3. Run `cdk diff` to verify changes
4. Submit a pull request
