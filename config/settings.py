from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings
from pathlib import Path
import os

class LogConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    file_path: Optional[str] = Field(default=None, description="Log file path")
    rotation: str = Field(default="1 day", description="Log rotation interval")
    retention: str = Field(default="1 week", description="Log retention period")

class IllumioConfig(BaseModel):
    """Illumio-specific configuration."""
    base_url: str = Field(..., description="Illumio PCE base URL")
    org_id: int = Field(..., description="Organization ID")
    api_version: str = Field(default="v2", description="API version")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    timeout: int = Field(default=30, description="API request timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    retry_delay: int = Field(default=1, description="Delay between retries in seconds")

class KubernetesConfig(BaseModel):
    """Kubernetes configuration."""
    namespace: str = Field(default="illumio-system", description="Default namespace")
    config_path: Optional[str] = Field(default=None, description="Kubeconfig file path")
    context: Optional[str] = Field(default=None, description="Kubernetes context")
    in_cluster: bool = Field(default=False, description="Running in cluster flag")

class Settings(BaseSettings):
    """Main application settings."""
    # Environment settings
    environment: str = Field(
        default="development",
        description="Application environment"
    )
    debug: bool = Field(default=False, description="Debug mode flag")
    
    # Application paths
    base_dir: str = Field(
        default=str(Path(__file__).parent.parent),
        description="Base directory path"
    )
    config_dir: str = Field(
        default=str(Path(__file__).parent),
        description="Configuration directory path"
    )
    
    # Component configurations
    logging: LogConfig = Field(default_factory=LogConfig, description="Logging configuration")
    kubernetes: KubernetesConfig = Field(
        default_factory=KubernetesConfig,
        description="Kubernetes configuration"
    )
    
    # Additional settings
    secret_key: str = Field(..., description="Application secret key")
    allowed_hosts: list[str] = Field(default=["*"], description="Allowed hosts")
    cors_origins: list[str] = Field(default=["*"], description="CORS allowed origins")
    
    # Custom settings
    custom_settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional custom settings"
    )

    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed = {'development', 'testing', 'staging', 'production'}
        if v.lower() not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v.lower()

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings
        ):
            """Customize settings loading order."""
            return (
                init_settings,
                env_settings,
                file_secret_settings,
            )

    def get_log_config(self) -> Dict[str, Any]:
        """Get logging configuration dictionary."""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'default': {
                    'format': self.logging.format
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'default',
                    'level': self.logging.level
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': self.logging.file_path or 'app.log',
                    'formatter': 'default',
                    'level': self.logging.level
                } if self.logging.file_path else None
            },
            'root': {
                'level': self.logging.level,
                'handlers': ['console', 'file'] if self.logging.file_path else ['console']
            }
        }

    def get_kubernetes_config(self) -> Dict[str, Any]:
        """Get Kubernetes configuration dictionary."""
        return self.kubernetes.model_dump()
