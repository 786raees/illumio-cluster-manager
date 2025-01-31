from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator, field_validator
from pathlib import Path
import os

class VaultAuth(BaseModel):
    """Vault authentication configuration."""
    method: str = Field(default="token", description="Authentication method")
    role_id: Optional[str] = Field(default=None, description="AppRole role ID")
    secret_id: Optional[str] = Field(default=None, description="AppRole secret ID")
    token: Optional[str] = Field(default=None, description="Auth token")
    mount_point: Optional[str] = Field(default=None, description="Auth mount point")

class VaultTLS(BaseModel):
    """Vault TLS configuration."""
    ca_cert: Optional[str] = Field(default=None, description="CA certificate path")
    client_cert: Optional[str] = Field(default=None, description="Client certificate path")
    client_key: Optional[str] = Field(default=None, description="Client key path")
    verify: bool = Field(default=True, description="Verify TLS certificates")

class VaultConfig(BaseModel):
    """Vault configuration settings."""
    # Connection settings
    url: str = Field(..., description="Vault server URL")
    namespace: Optional[str] = Field(default=None, description="Vault namespace")
    
    # Authentication
    auth: VaultAuth = Field(default_factory=VaultAuth, description="Authentication settings")
    
    # TLS/SSL settings
    tls: VaultTLS = Field(default_factory=VaultTLS, description="TLS configuration")
    
    # Retry settings
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    retry_delay: float = Field(default=0.1, description="Delay between retries in seconds")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    
    # Secret engine settings
    mount_point: str = Field(default="secret", description="Secret engine mount point")
    secret_path: str = Field(
        default="illumio-cluster-manager",
        description="Base path for secrets"
    )
    
    # Additional settings
    custom_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Custom headers for requests"
    )
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        """Validate Vault URL."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v.rstrip('/')
    
    @property
    def client_config(self) -> Dict[str, Any]:
        """Get configuration for hvac client."""
        config = {
            'url': self.url,
            'timeout': self.timeout,
            'verify': self.tls.verify,
        }
        
        # Add TLS configuration
        if self.tls.ca_cert:
            config['verify'] = self.tls.ca_cert
        if self.tls.client_cert and self.tls.client_key:
            config['cert'] = (self.tls.client_cert, self.tls.client_key)
            
        # Add namespace if specified
        if self.namespace:
            config['namespace'] = self.namespace
            
        # Add custom headers
        if self.custom_headers:
            config['headers'] = self.custom_headers
            
        return config
    
    def get_secret_path(self, path: str) -> str:
        """Get full path for a secret.
        
        Args:
            path: Relative secret path
            
        Returns:
            str: Full secret path
        """
        return f"{self.mount_point}/data/{self.secret_path.strip('/')}/{path.strip('/')}"
    
    class Config:
        """Pydantic configuration."""
        env_prefix = "VAULT_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
