import pytest
from app.utils.exceptions import IllumioError, ClusterOperationError
from app.utils import IllumioEnforcementMode

@pytest.mark.asyncio
class TestIllumioService:
    """Test suite for IllumioService."""

    async def test_get_cluster_success(
        self,
        mock_illumio_service,
        mock_api_client,
        sample_cluster_data
    ):
        """Test successful cluster retrieval."""
        # Setup
        mock_api_client.request.return_value = [sample_cluster_data]
        mock_illumio_service.api = mock_api_client
        
        # Execute
        cluster = await mock_illumio_service.get_cluster("test-cluster")
        
        # Assert
        assert cluster is not None
        assert cluster.name == "test-cluster"
        assert cluster.enforcement_mode == "visibility_only"
        mock_api_client.request.assert_called_once()

    async def test_get_cluster_not_found(
        self,
        mock_illumio_service,
        mock_api_client
    ):
        """Test cluster retrieval when not found."""
        # Setup
        mock_api_client.request.return_value = []
        mock_illumio_service.api = mock_api_client
        
        # Execute
        cluster = await mock_illumio_service.get_cluster("non-existent")
        
        # Assert
        assert cluster is None
        mock_api_client.request.assert_called_once()

    async def test_create_cluster_success(
        self,
        mock_illumio_service,
        mock_api_client,
        mock_vault_client,
        sample_cluster_data
    ):
        """Test successful cluster creation."""
        # Setup
        mock_api_client.request.return_value = sample_cluster_data
        mock_illumio_service.api = mock_api_client
        mock_illumio_service.vault = mock_vault_client
        
        # Execute
        cluster = await mock_illumio_service.create_cluster(
            "test-cluster",
            description="Test Cluster",
            enforcement_mode=IllumioEnforcementMode.VISIBILITY_ONLY
        )
        
        # Assert
        assert cluster is not None
        assert cluster.name == "test-cluster"
        assert cluster.enforcement_mode == "visibility_only"
        mock_api_client.request.assert_called_once()
        mock_vault_client.store_secret.assert_called_once()

    async def test_create_cluster_failure(
        self,
        mock_illumio_service,
        mock_api_client
    ):
        """Test cluster creation failure."""
        # Setup
        mock_api_client.request.side_effect = Exception("API Error")
        mock_illumio_service.api = mock_api_client
        
        # Execute and Assert
        with pytest.raises(ClusterOperationError):
            await mock_illumio_service.create_cluster("test-cluster")

    async def test_delete_cluster_success(
        self,
        mock_illumio_service,
        mock_api_client,
        mock_vault_client,
        sample_cluster_data
    ):
        """Test successful cluster deletion."""
        # Setup
        mock_api_client.request.side_effect = [
            [sample_cluster_data],  # get_cluster response
            None  # delete response
        ]
        mock_illumio_service.api = mock_api_client
        mock_illumio_service.vault = mock_vault_client
        
        # Execute
        result = await mock_illumio_service.delete_cluster("test-cluster")
        
        # Assert
        assert result is True
        assert mock_api_client.request.call_count == 2
        mock_vault_client.delete_secret_versions.assert_called_once()

    async def test_delete_cluster_not_found(
        self,
        mock_illumio_service,
        mock_api_client
    ):
        """Test cluster deletion when not found."""
        # Setup
        mock_api_client.request.return_value = []
        mock_illumio_service.api = mock_api_client
        
        # Execute
        result = await mock_illumio_service.delete_cluster("non-existent")
        
        # Assert
        assert result is False
        mock_api_client.request.assert_called_once()

    async def test_create_namespace_profile_success(
        self,
        mock_illumio_service,
        mock_api_client,
        sample_profile_data
    ):
        """Test successful namespace profile creation."""
        # Setup
        mock_api_client.request.return_value = sample_profile_data
        mock_illumio_service.api = mock_api_client
        
        # Execute
        profile = await mock_illumio_service.create_namespace_profile(
            "123",
            "test-namespace"
        )
        
        # Assert
        assert profile is not None
        assert profile.namespace == "test-namespace"
        assert profile.managed is True
        mock_api_client.request.assert_called_once()

    async def test_create_namespace_profile_invalid_namespace(
        self,
        mock_illumio_service
    ):
        """Test namespace profile creation with invalid namespace."""
        # Execute and Assert
        with pytest.raises(ValueError):
            await mock_illumio_service.create_namespace_profile(
                "123",
                "invalid namespace"
            )

    async def test_get_or_create_label_existing(
        self,
        mock_illumio_service,
        mock_api_client,
        sample_label_data
    ):
        """Test getting existing label."""
        # Setup
        mock_api_client.request.return_value = [sample_label_data]
        mock_illumio_service.api = mock_api_client
        
        # Execute
        label = await mock_illumio_service.get_or_create_label("env", "test")
        
        # Assert
        assert label is not None
        assert label.key == "env"
        assert label.value == "test"
        mock_api_client.request.assert_called_once()

    async def test_get_or_create_label_new(
        self,
        mock_illumio_service,
        mock_api_client,
        sample_label_data
    ):
        """Test creating new label."""
        # Setup
        mock_api_client.request.side_effect = [
            [],  # get response
            sample_label_data  # create response
        ]
        mock_illumio_service.api = mock_api_client
        
        # Execute
        label = await mock_illumio_service.get_or_create_label("env", "test")
        
        # Assert
        assert label is not None
        assert label.key == "env"
        assert label.value == "test"
        assert mock_api_client.request.call_count == 2
