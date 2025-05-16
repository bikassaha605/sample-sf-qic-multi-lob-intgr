# **Pre-requisites**

1. **AWS Environment**
   - Active AWS Account with appropriate access
   - AWS CLI installed and configured
   - AWS CDK CLI installed
   - Target region access and permissions
3. **Amazon Connect**
   - Active Amazon Connect instance
   - Configured Connect queue
   - Connect administrator access
4. **Salesforce**
   - Salesforce org with API access
   - Knowledge base implementation
   - Appropriate Salesforce access
   - Connected App setup permissions - https://help.salesforce.com/articleView?id=connected_app_overview.htm
5. AppFlow
   - Salesforce Connector for AppFlow  - https://docs.aws.amazon.com/appflow/latest/userguide/salesforce.html#salesforce-setup
6. **Development Environment**
   - Python 3.x
   - Git
   - Code editor
   - AWS CDK development experience
7. **Security Access**
   - Appropriate IAM permissions
   - Appropriate Salesforce access
   - Amazon AppFlow Service access

### 

# Configuration Details

### **AWS Configuration**

```
{
"account": "Your-AWS-Account-ID",
"region": "Your-Target-Region",
"env_name": "Environment-Name"
}
```

### **Amazon Connect Setup**

```
{
  "connect": {
    "instance_id": "Your-Connect-Instance-ID",
    "queue_id": "Your-Connect-Queue-ID"
  }
}
```

### **Salesforce AppFlow Configuration**

    * Create AppFlow connection 
    * Required permissions for Salesforce:
        a. Knowledge object read access
        b. API access enabled
        c. OAuth scopes configured

### **Knowledge Base Mapping**

    * Define your Lines of Business (LOBs)

```
 "LOBs": [
        "LOB1",
        "LOB2",
        "LOB3"
    ]
```

    * Map required fields:

```
"businessUnitFilters": {
  "YourLOB1": {
    "field": "Your-Classification-Field",
    "value": "LOB1-Value"
  }
  // Add more LOBs as needed
}
```

### **AppFlow-Salesforce  Configuration**

```
{
  "connection_name": "dev-sf-connection",  // Replace with your AppFlow connection name
  "object_name": "Knowledge__kav",         
}
```

### **Knowledge Article Fields**

```
"projections": [
  // System Required Fields
  {"field": "Id", "data_type": "id"},
  {"field": "LastModifiedDate", "data_type": "datetime"},
  {"field": "ArticleNumber", "data_type": "string"},
  {"field": "PublishStatus", "data_type": "picklist"},  
  {"field": "UrlName", "data_type": "string"}
  
  // Custom Fields - Replace with your actual fields
  {"field": "Your-Title-Field", "data_type": "string"},
  {"field": "Your-Content-Field", "data_type": "textarea"},
  
  // Add additional fields as needed
]
```

### Salesforce Knowledge Filter

```
"filters": [
  {
    "field": "PublishStatus",
    "operator": "EQUAL_TO",
    "values": ["Online", "Archived"]
  }
  // Add additional filters as needed
]
```

### Salesforce Knowledge Validation Rules

```
"validations": [
  {
    "field": "Your-Content-Field", // Replace with your content field. Must be in the list of Projections above
    "operator": "VALIDATE_NON_NULL",
    "action": "DropRecord"
  }
  // Add additional validations as needed
]
```

## Important Notes:

* The connection_name  must match your Amazon AppFlow-Salesforce connection name exactly
* The object_name  should be Knowledge__kav
* Ensure the AppFlow connection has proper permissions to access the specified object
* Test connection and object access before deployment
* Document any custom object names or connection names used
* Keep configuration consistent across environments
* Validate object permissions and field accessibility



# Deploying the CDK

### Clone and Configure Project

```
# Clone the repository
git clone <repository-url>
cd <project folder>

```

### Install Dependencies

```
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Bootstrap CDK Environment

If this is your first time using CDK in this account/region:

```
cdk bootstrap aws://ACCOUNT-NUMBER/REGION
```

### Review CDK Diff

```
cdk diff
```

### Deploy the Stack

```
cdk deploy
```

The deployment will create the following resources:

* Amazon AppFlow flow for Salesforce integration
* Lambda functions for data processing
* IAM roles and policies
* Amazon Q knowledge bases
* Amazon Connect integration components

### Verify Deployment

After deployment completes:

* Check AWS CloudFormation console for stack status
* Verify AppFlow flow creation
* Confirm Lambda functions deployment
* Check Amazon Q knowledge bases setup
* Validate Amazon Connect integration

### Post-Deployment Steps

* Run the AppFlows
    * Sign in the AWS Management Console and open the Amazon AppFlow console at https://console.aws.amazon.com/appflow/
    * In the navigation pane on the left, choose **Flows**. The console shows the **Flows** page. This page contains a table that summarizes the flows that are created.
    * To initiate a flow, you _activate_ or _run_ it. We have 2 types of flows created: **OnDemand** and **Scheduled**
    * For each LOB, Select the OnDemand flow and choose **View Details**.
    * Choose **Run flow** to run the flow.
![Alt text](https://github.com/bhaskar27in/sf-qic-multi-lob-intgr/blob/main/images/onDemand-flow.jpg) 
    * For each LOB, Select the Scheduled flow and choose **View Details**
    * Choose **Activate** to activate the flow
![Alt text](https://github.com/bhaskar27in/sf-qic-multi-lob-intgr/blob/main/images/scheduled-flow.jpg)
  
* Review and update the Amazon Connect contact flow
    * Log in to your Amazon Connect instance
    * Under **Routing**, choose **Contact Flows**.
    * Choose the flow named: **qic-sf-contact-flow**
    * Navigate to the **Get customer input** Block
    * Update the Prompts to include your BUs or LOBs
    * Update the Set contact attributes block for each options. The LOB attribute is mandatory, and the value should be the same as the ones provided in the CDK configuration at the time of deployment
![Alt text](https://github.com/bhaskar27in/sf-qic-multi-lob-intgr/blob/main/images/cf1.png)
    * Click **Save** to save the flow
    * Click **Publish** to publish the flow
    
* Verify the AppFlow flow status. 
    * Trigger the OnDemand Flow first - to retrieve the existing knowledge content from Salesforce
    * Start the Scheduled Flow - to periodically poll Salesforce Knowledge too import any additions/updates to the Salesforce Knowledge.
* Verify target s3 buckets for Salesforce data synchronization
* Monitor CloudWatch logs

## Troubleshooting Tips

### Common Issues and Solutions

* **AppFlow Connection Issues**
    * Verify connection_name in config
    * Check Salesforce credentials
    * Validate OAuth token
* **Permission Errors**
    * Review IAM roles
    * Verify Salesforce API access
* **Knowledge Base Sync Issues**
    * Validate object_name configuration
    * Check field mappings
