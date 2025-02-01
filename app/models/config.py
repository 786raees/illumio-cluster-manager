from typing import Optional, Dict, Any
from pydantic import BaseModel, AnyUrl, SecretStr, Field, field_validator, model_validator
from app.utils import Environment, LogLevel, PATTERNS, ValidationHelper

class Settings(BaseModel):
    """Application settings model with validation."""
    
    # Environment settings
    environment: Environment = Environment.DEVELOPMENT
    log_level: LogLevel = LogLevel.INFO
    verify_ssl: bool = True
    max_retries: int = Field(default=3, ge=1, le=10)
    
    # Illumio PCE settings
    base_url: AnyUrl = Field(..., env='ILLUMIO_BASE_URL')
    org_id: str = Field(..., pattern=r'^\d+$', env='ILLUMIO_ORG_ID')
    api_key: Optional[SecretStr] = Field(None, env='ILLUMIO_API_KEY')
    api_user: Optional[str] = Field(None, env='ILLUMIO_API_USER')
    
    # Vault settings
    vault_addr: AnyUrl = Field(..., env='VAULT_ADDR')
    vault_token: SecretStr = Field(..., env='VAULT_TOKEN')
    vault_mount: str = "secret"
    vault_path: str = "illumio"
    
    # Cluster settings
    cluster_id: Optional[str] = Field(None, env='CLUSTER_ID')
    cluster_name: Optional[str] = Field(None, env='CLUSTER_NAME')
    cluster_token: Optional[SecretStr] = Field(None, env='CLUSTER_TOKEN')
    cluster_namespace: str = "illumio-system"
    
    # Logging settings
    log_file: Optional[str] = None
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_max_bytes: int = Field(default=10 * 1024 * 1024, ge=1024)  # 10MB
    log_backup_count: int = Field(default=5, ge=1, le=20)
    
    # Additional settings
    extra_headers: Dict[str, str] = Field(default_factory=dict)
    timeout: float = Field(default=30.0, ge=1.0, le=300.0)
    
    @field_validator('cluster_name')
    @classmethod
    def validate_cluster_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate cluster name format."""
        if v is not None and not ValidationHelper.is_valid_cluster_name(v):
            raise ValueError(f"Invalid cluster name format: {v}")
        return v
    
    @field_validator('cluster_namespace')
    @classmethod
    def validate_namespace(cls, v: str) -> str:
        """Validate Kubernetes namespace format."""
        if not ValidationHelper.is_valid_namespace(v):
            raise ValueError(f"Invalid namespace format: {v}")
        return v
    
    @field_validator('org_id')
    @classmethod
    def validate_org_id(cls, v: str) -> str:
        """Validate organization ID format."""
        if not v.isdigit():
            raise ValueError("Organization ID must be numeric")
        return v
    
    @model_validator(mode='after')
    def validate_auth_credentials(self) -> 'Settings':
        """Validate that either API key or user credentials are provided."""
        if bool(self.api_key) == bool(self.api_user):
            raise ValueError("Either api_key or api_user must be provided, but not both")
        return self
    
    @model_validator(mode='after')
    def validate_cluster_settings(self) -> 'Settings':
        """Validate cluster settings consistency."""
        if self.cluster_id and not self.cluster_name:
            raise ValueError("cluster_name is required when cluster_id is provided")
        if self.cluster_token and not self.cluster_id:
            raise ValueError("cluster_id is required when cluster_token is provided")
        return self
    
    class Config:
        """Pydantic model configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        secrets_dir = "/var/run/secrets"
        
        # Allow extra fields for future extensibility
        extra = 'allow' 