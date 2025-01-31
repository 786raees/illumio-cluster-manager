from typing import Optional, Any

class IllumioClusterManagerError(Exception):
    """Base exception class for Illumio Cluster Manager."""
    
    def __init__(self, message: str, details: Optional[Any] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)

class ConfigurationError(IllumioClusterManagerError):
    """Raised when there's an error in configuration."""
    pass

class APIError(IllumioClusterManagerError):
    """Raised when there's an error in API communication."""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response

class APIConnectionError(APIError):
    """Raised when there's a network or connection error."""
    pass

class ValidationError(IllumioClusterManagerError):
    """Raised when validation fails."""
    pass

class VaultError(IllumioClusterManagerError):
    """Raised when there's an error with Vault operations."""
    pass

class VaultIntegrationError(VaultError):
    """Raised when there's an error with Vault integration."""
    pass

class VaultAuthenticationError(VaultError):
    """Raised when Vault authentication fails."""
    pass

class KubernetesError(IllumioClusterManagerError):
    """Raised when there's an error with Kubernetes operations."""
    pass

class ResourceNotFoundError(IllumioClusterManagerError):
    """Raised when a requested resource is not found."""
    pass

class AuthenticationError(IllumioClusterManagerError):
    """Raised when authentication fails."""
    pass

class PermissionError(IllumioClusterManagerError):
    """Raised when permission is denied for an operation."""
    pass

class IllumioError(IllumioClusterManagerError):
    """Raised when there's an error specific to Illumio operations."""
    pass

class ClusterOperationError(IllumioError):
    """Raised when cluster operations fail."""
    pass

class LabelOperationError(IllumioError):
    """Raised when label operations fail."""
    pass 