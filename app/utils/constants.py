from enum import Enum
from typing import Dict, Any

class Environment(str, Enum):
    """Environment enumeration."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class LogLevel(str, Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class HTTPMethod(str, Enum):
    """HTTP method enumeration."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"

class IllumioRole(str, Enum):
    """Illumio role enumeration."""
    CONTAINER = "Container"
    CLUSTER_NODE = "Cluster Node"
    WORKLOAD = "Workload"

class IllumioEnforcementMode(str, Enum):
    """Illumio enforcement mode enumeration."""
    VISIBILITY_ONLY = "visibility_only"
    SELECTIVE = "selective"
    FULL = "full"

# Default configuration values
DEFAULT_CONFIG: Dict[str, Any] = {
    "log_level": LogLevel.INFO,
    "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "max_retries": 3,
    "timeout": 30,
    "chunk_size": 8192,
    "max_workers": 4
}

# API related constants
API_VERSION = "v2"
DEFAULT_API_TIMEOUT = 30
MAX_PAGE_SIZE = 100
DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Kubernetes related constants
K8S_NAMESPACE = "illumio-system"
K8S_SERVICE_ACCOUNT = "illumio-service"
K8S_CONFIG_MAP = "illumio-config"
K8S_SECRET = "illumio-secret"

# Vault related constants
VAULT_DEFAULT_MOUNT = "secret"
VAULT_DEFAULT_PATH = "illumio"
VAULT_TOKEN_TTL = "1h"

# Illumio related constants
ILLUMIO_API_VERSION = "v2"
ILLUMIO_DEFAULT_PORT = 8443
ILLUMIO_DEFAULT_PROTOCOL = "https"

ILLUMIO_ENDPOINTS = {
    "container_clusters": "container_clusters",
    "container_workload_profiles": "container_workload_profiles",
    "labels": "labels",
    "pairing_profiles": "pairing_profiles",
    "pairing_keys": "pairing_keys",
    "sec_policy": "sec_policy"
}

ILLUMIO_LABEL_TYPES = {
    "role": "role",
    "app": "app",
    "env": "env",
    "loc": "loc",
    "cluster": "cluster",
    "namespace": "namespace"
}

ILLUMIO_DEFAULT_SETTINGS = {
    "enforcement_mode": IllumioEnforcementMode.VISIBILITY_ONLY,
    "visibility_level": "flow_summary",
    "log_traffic": False,
    "log_traffic_lock": True,
    "enforcement_mode_lock": True
}

# Regex patterns
PATTERNS = {
    "cluster_name": r"^[a-z0-9][a-z0-9-]*[a-z0-9]$",
    "namespace": r"^[a-z0-9][a-z0-9-]*[a-z0-9]$",
    "label_key": r"^[a-z0-9A-Z][a-z0-9A-Z._/-]*[a-z0-9A-Z]$",
    "label_value": r"^[a-z0-9A-Z][a-z0-9A-Z._/-]*[a-z0-9A-Z]$",
    "hostname": r"^[a-zA-Z0-9][-a-zA-Z0-9.]*[a-zA-Z0-9]$",
    "ip_address": r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
}

# Error messages
ERROR_MESSAGES = {
    "config_not_found": "Configuration file not found: {path}",
    "invalid_config": "Invalid configuration: {details}",
    "api_error": "API request failed: {status_code} - {message}",
    "vault_error": "Vault operation failed: {message}",
    "k8s_error": "Kubernetes operation failed: {message}",
    "validation_error": "Validation failed: {message}",
    "resource_not_found": "Resource not found: {resource_type} - {resource_name}",
    "auth_error": "Authentication failed: {message}",
    "permission_error": "Permission denied: {message}",
    "cluster_error": "Cluster operation failed: {message}",
    "label_error": "Label operation failed: {message}",
    "pairing_error": "Pairing operation failed: {message}",
    "policy_error": "Policy operation failed: {message}"
} 