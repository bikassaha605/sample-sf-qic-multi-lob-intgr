#!/usr/bin/env python3

import os
import json
from aws_cdk import App, Environment
from connect_q_cdk.stacks.connect_q_stack import ConnectQStack
from connect_q_cdk.common.resource_manager import ResourceManager

def get_config():
    """Load configuration based on environment."""
    env = os.getenv('ENV', 'dev')
    config_path = os.path.join('config', f'config.{env}.json')
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            'vpc_id': os.getenv('VPC_ID', ''),
            'env_name': env,
            'account': os.getenv('CDK_DEFAULT_ACCOUNT', ''),
            'region': os.getenv('CDK_DEFAULT_REGION', 'us-west-2')
        }

app = App()

config = get_config()
resource_manager = ResourceManager(config)

stack = ConnectQStack(
    app,
    f"{config['env_name']}-connect-q",
    resource_manager=resource_manager,
    env=Environment(
        account=config['account'],
        region=config['region']
    )
)

app.synth()
