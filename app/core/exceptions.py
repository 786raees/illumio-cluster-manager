class IllumioManagerError(Exception):
    """Base exception for all custom exceptions"""
    pass

class APIConnectionError(IllumioManagerError):
    """Exception for API communication failures"""
    pass

class AuthenticationError(IllumioManagerError):
    """Exception for authentication failures"""
    pass

class ConfigurationError(IllumioManagerError):
    """Exception for configuration errors"""
    pass

class VaultIntegrationError(IllumioManagerError):
    """Exception for Vault operation failures"""
    pass