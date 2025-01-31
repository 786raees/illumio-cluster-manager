import hvac
from typing import Optional, Dict, Any, List
from app.utils import (
    get_logger,
    VaultError,
    VaultIntegrationError,
    VaultAuthenticationError,
    DataHelper,
    TimeHelper,
    VAULT_DEFAULT_MOUNT,
    VAULT_DEFAULT_PATH,
    VAULT_TOKEN_TTL,
    retry,
    log_execution
)
from app.models.config import Settings

class VaultClient:
    """HashiCorp Vault client with enhanced functionality."""

    def __init__(self, settings: Settings):
        """Initialize Vault client.
        
        Args:
            settings: Application settings
            
        Raises:
            VaultAuthenticationError: If authentication fails
        """
        self.settings = settings
        self.logger = get_logger(__name__)
        self.client = self._create_client()
        self.mount_point = getattr(settings, 'vault_mount', VAULT_DEFAULT_MOUNT)
        
    def _create_client(self) -> hvac.Client:
        """Initialize and authenticate Vault client.
        
        Returns:
            hvac.Client: Authenticated Vault client
            
        Raises:
            VaultAuthenticationError: If authentication fails
            VaultIntegrationError: If client creation fails
        """
        try:
            client = hvac.Client(
                url=str(self.settings.vault_addr),
                token=self.settings.vault_token.get_secret_value(),
                verify=self.settings.verify_ssl
            )
            
            if not client.is_authenticated():
                raise VaultAuthenticationError("Failed to authenticate with Vault")
                
            return client
            
        except hvac.exceptions.VaultError as e:
            raise VaultIntegrationError(f"Failed to create Vault client: {str(e)}")
        except Exception as e:
            raise VaultIntegrationError(f"Unexpected error creating Vault client: {str(e)}")

    @retry(max_attempts=3)
    @log_execution(level="DEBUG")
    def store_secret(
        self,
        path: str,
        secret_data: Dict[str, Any],
        mount_point: Optional[str] = None,
        cas: Optional[int] = None
    ) -> bool:
        """Store secret with versioning and CAS check.
        
        Args:
            path: Secret path
            secret_data: Secret data to store
            mount_point: Vault mount point
            cas: Check-and-Set value
            
        Returns:
            bool: True if successful
            
        Raises:
            VaultError: If secret storage fails
        """
        try:
            mount_point = mount_point or self.mount_point
            path = f"{VAULT_DEFAULT_PATH}/{path}".strip('/')
            
            self.logger.debug(
                f"Storing secret at {path}",
                extra={'mount_point': mount_point}
            )
            
            response = self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secret_data,
                mount_point=mount_point,
                cas=cas
            )
            
            version = DataHelper.safe_get(response, 'data', 'version')
            return version is not None and version > 0
            
        except hvac.exceptions.VaultError as e:
            raise VaultError(f"Failed to store secret: {str(e)}")

    @retry(max_attempts=3)
    @log_execution(level="DEBUG")
    def get_secret(
        self,
        path: str,
        mount_point: Optional[str] = None,
        version: Optional[int] = None
    ) -> Dict[str, Any]:
        """Retrieve secret with version support.
        
        Args:
            path: Secret path
            mount_point: Vault mount point
            version: Secret version
            
        Returns:
            Dict[str, Any]: Secret data
            
        Raises:
            VaultError: If secret retrieval fails
        """
        try:
            mount_point = mount_point or self.mount_point
            path = f"{VAULT_DEFAULT_PATH}/{path}".strip('/')
            
            self.logger.debug(
                f"Retrieving secret from {path}",
                extra={
                    'mount_point': mount_point,
                    'version': version
                }
            )
            
            try:
                response = self.client.secrets.kv.v2.read_secret_version(
                    path=path,
                    mount_point=mount_point,
                    version=version
                )
                return DataHelper.safe_get(response, 'data', 'data', default={})
                
            except hvac.exceptions.InvalidPath:
                self.logger.warning(f"Secret not found at path: {path}")
                return {}
                
        except hvac.exceptions.VaultError as e:
            raise VaultError(f"Failed to retrieve secret: {str(e)}")

    @retry(max_attempts=3)
    @log_execution(level="DEBUG")
    def delete_secret_versions(
        self,
        path: str,
        versions: List[int],
        mount_point: Optional[str] = None
    ) -> bool:
        """Permanently delete specific secret versions.
        
        Args:
            path: Secret path
            versions: List of versions to delete
            mount_point: Vault mount point
            
        Returns:
            bool: True if successful
            
        Raises:
            VaultError: If deletion fails
        """
        try:
            mount_point = mount_point or self.mount_point
            path = f"{VAULT_DEFAULT_PATH}/{path}".strip('/')
            
            self.logger.debug(
                f"Deleting secret versions at {path}",
                extra={
                    'mount_point': mount_point,
                    'versions': versions
                }
            )
            
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=path,
                mount_point=mount_point
            )
            return True
            
        except hvac.exceptions.VaultError as e:
            raise VaultError(f"Failed to delete secret versions: {str(e)}")

    @log_execution(level="DEBUG")
    def list_secrets(
        self,
        path: str = "",
        mount_point: Optional[str] = None
    ) -> List[str]:
        """List secrets at specified path.
        
        Args:
            path: Path to list secrets from
            mount_point: Vault mount point
            
        Returns:
            List[str]: List of secret names
            
        Raises:
            VaultError: If listing fails
        """
        try:
            mount_point = mount_point or self.mount_point
            path = f"{VAULT_DEFAULT_PATH}/{path}".strip('/')
            
            response = self.client.secrets.kv.v2.list_secrets(
                path=path,
                mount_point=mount_point
            )
            
            return DataHelper.safe_get(response, 'data', 'keys', default=[])
            
        except hvac.exceptions.VaultError as e:
            raise VaultError(f"Failed to list secrets: {str(e)}")

    def is_authenticated(self) -> bool:
        """Check if client is authenticated.
        
        Returns:
            bool: True if authenticated
        """
        return self.client.is_authenticated()