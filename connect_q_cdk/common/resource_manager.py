"""Resource Manager for CDK stacks."""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Config:
    """Configuration class for stack resources."""
    vpc_id: str
    env_name: str
    account: str
    region: str

class ResourceManager:
    """Manages resource naming and configuration."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize ResourceManager with configuration."""
        self._raw_config = config
        self.config = Config(
            vpc_id=config.get('vpc_id', ''),
            env_name=config.get('env_name', 'dev'),
            account=config.get('account', ''),
            region=config.get('region', 'us-west-2')
        )
        self.env_name = self.config.env_name

    @property
    def raw_config(self) -> Dict[str, Any]:
        """Get the raw configuration dictionary."""
        return self._raw_config

    def generate_resource_name(self, resource_type: str, resource_name: str) -> str:
        """Generate a standardized resource name."""
        return f"{self.env_name}-{resource_type}-{resource_name}"

    def generate_resource_export_name(self, stack_name: str, resource_type: str, resource_name: str) -> str:
        """Generate a standardized export name for CloudFormation exports."""
        return f"{stack_name}-{self.env_name}-{resource_type}-{resource_name}"
