import pytest
from app.utils.exceptions import VaultIntegrationError, VaultAuthenticationError

@pytest.mark.asyncio
class TestVaultClient:
    """Test suite for VaultClient."""

    async def test_authenticate_token_success(
        self,
        mock_vault_client,
        mock_vault_config
    ):
        """Test successful token authentication."""
        # Setup
        mock_vault_client.client.auth.token.lookup_self.return_value = {
            "data": {"id": "test-token"}
        }
        
        # Execute
        await mock_vault_client.authenticate()
        
        # Assert
        mock_vault_client.client.auth.token.lookup_self.assert_called_once()

    async def test_authenticate_token_failure(
        self,
        mock_vault_client,
        mock_vault_config
    ):
        """Test token authentication failure."""
        # Setup
        mock_vault_client.client.auth.token.lookup_self.side_effect = Exception(
            "Invalid token"
        )
        
        # Execute and Assert
        with pytest.raises(VaultAuthenticationError):
            await mock_vault_client.authenticate()

    async def test_authenticate_approle_success(
        self,
        mock_vault_client,
        mock_vault_config
    ):
        """Test successful AppRole authentication."""
        # Setup
        mock_vault_config.auth.method = "approle"
        mock_vault_config.auth.role_id = "test-role"
        mock_vault_config.auth.secret_id = "test-secret"
        mock_vault_client.client.auth.approle.login.return_value = {
            "auth": {"client_token": "new-token"}
        }
        
        # Execute
        await mock_vault_client.authenticate()
        
        # Assert
        mock_vault_client.client.auth.approle.login.assert_called_once_with(
            role_id="test-role",
            secret_id="test-secret"
        )

    async def test_store_secret_success(
        self,
        mock_vault_client
    ):
        """Test successful secret storage."""
        # Setup
        secret_path = "test/secret"
        secret_data = {"key": "value"}
        
        # Execute
        await mock_vault_client.store_secret(secret_path, secret_data)
        
        # Assert
        mock_vault_client.client.secrets.kv.v2.create_or_update_secret.assert_called_once()

    async def test_store_secret_failure(
        self,
        mock_vault_client
    ):
        """Test secret storage failure."""
        # Setup
        mock_vault_client.client.secrets.kv.v2.create_or_update_secret.side_effect = \
            Exception("Storage failed")
        
        # Execute and Assert
        with pytest.raises(VaultIntegrationError):
            await mock_vault_client.store_secret("test/secret", {"key": "value"})

    async def test_get_secret_success(
        self,
        mock_vault_client
    ):
        """Test successful secret retrieval."""
        # Setup
        secret_path = "test/secret"
        mock_vault_client.client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {
                "data": {"key": "value"}
            }
        }
        
        # Execute
        result = await mock_vault_client.get_secret(secret_path)
        
        # Assert
        assert result == {"key": "value"}
        mock_vault_client.client.secrets.kv.v2.read_secret_version.assert_called_once()

    async def test_get_secret_not_found(
        self,
        mock_vault_client
    ):
        """Test secret retrieval when not found."""
        # Setup
        mock_vault_client.client.secrets.kv.v2.read_secret_version.side_effect = \
            Exception("Secret not found")
        
        # Execute and Assert
        with pytest.raises(VaultIntegrationError):
            await mock_vault_client.get_secret("test/secret")

    async def test_delete_secret_success(
        self,
        mock_vault_client
    ):
        """Test successful secret deletion."""
        # Setup
        secret_path = "test/secret"
        
        # Execute
        await mock_vault_client.delete_secret_versions(secret_path, [1, 2, 3])
        
        # Assert
        mock_vault_client.client.secrets.kv.v2.delete_metadata_and_all_versions.\
            assert_called_once_with(
                path=secret_path
            )

    async def test_delete_secret_failure(
        self,
        mock_vault_client
    ):
        """Test secret deletion failure."""
        # Setup
        mock_vault_client.client.secrets.kv.v2.delete_metadata_and_all_versions.\
            side_effect = Exception("Deletion failed")
        
        # Execute and Assert
        with pytest.raises(VaultIntegrationError):
            await mock_vault_client.delete_secret_versions("test/secret", [1, 2, 3])

    async def test_list_secrets_success(
        self,
        mock_vault_client
    ):
        """Test successful secrets listing."""
        # Setup
        mock_vault_client.client.secrets.kv.v2.list_secrets.return_value = {
            "data": {
                "keys": ["secret1", "secret2"]
            }
        }
        
        # Execute
        result = await mock_vault_client.list_secrets("test")
        
        # Assert
        assert result == ["secret1", "secret2"]
        mock_vault_client.client.secrets.kv.v2.list_secrets.assert_called_once()

    async def test_list_secrets_empty(
        self,
        mock_vault_client
    ):
        """Test listing secrets when none exist."""
        # Setup
        mock_vault_client.client.secrets.kv.v2.list_secrets.return_value = {
            "data": {
                "keys": []
            }
        }
        
        # Execute
        result = await mock_vault_client.list_secrets("test")
        
        # Assert
        assert result == []
        mock_vault_client.client.secrets.kv.v2.list_secrets.assert_called_once()
