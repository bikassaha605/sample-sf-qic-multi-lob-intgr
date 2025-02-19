"""Lambda Layer Version configuration."""

import os
import subprocess
import sys
from pathlib import Path
from aws_cdk import (
    aws_lambda as lambda_,
    aws_s3_assets as s3_assets,
)
from constructs import Construct

class LambdaLayerVersion(lambda_.LayerVersion):
    """Creates a Lambda Layer Version from a directory."""

    def __init__(
        self,
        scope: Construct,
        id_: str,
        layer_version_name: str,
        directory: str,
        **kwargs
    ) -> None:
        """Initialize Lambda Layer Version.
        
        Args:
            scope: CDK Construct scope
            id_: Unique identifier for the construct
            layer_version_name: Name for the layer version
            directory: Path to the directory containing layer code
            **kwargs: Additional arguments passed to LayerVersion
        """
        # Build the layer before creating the asset
        layer_path = Path(directory)
        build_script = Path(__file__).parent.parent / "layers" / "build_layer.py"
        
        try:
            subprocess.run([
                sys.executable,
                str(build_script),
                str(layer_path)
            ], check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to build layer {id_}: {e}")
            
        # Create asset from the built layer
        asset = s3_assets.Asset(
            scope,
            f"{id_}Asset",
            path=directory
        )

        super().__init__(
            scope,
            id_,
            layer_version_name=layer_version_name,
            code=lambda_.Code.from_bucket(
                asset.bucket,
                asset.s3_object_key
            ),
            compatible_runtimes=[
                lambda_.Runtime.PYTHON_3_10,
                lambda_.Runtime.PYTHON_3_11,
                lambda_.Runtime.PYTHON_3_12,
                lambda_.Runtime.PYTHON_3_13
            ],
            **kwargs
        )
