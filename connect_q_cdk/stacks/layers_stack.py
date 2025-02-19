"""CDK Stack for Lambda Layers."""

from aws_cdk import (
    NestedStack,
    aws_lambda as lambda_
)
from constructs import Construct
from ..common.lambda_layer_version import LambdaLayerVersion
from ..common.resource_manager import ResourceManager

class LayersNestedStack(NestedStack):
    """Nested stack for managing Lambda layers."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        resource_manager: ResourceManager,
        **kwargs
    ) -> None:
        """Initialize Layers Nested Stack.
        
        Args:
            scope: CDK Construct scope
            construct_id: Unique identifier for the construct
            resource_manager: Resource manager instance
            **kwargs: Additional arguments passed to NestedStack
        """
        super().__init__(scope, construct_id, **kwargs)

        # Create API Layer
        self.api_layer = LambdaLayerVersion(
            self,
            resource_manager.generate_resource_name("Layer", "api"),
            layer_version_name=resource_manager.generate_resource_name("Layer", "api"),
            directory="connect_q_cdk/layers/api_layer",
            description="Common API utilities layer"
        )
