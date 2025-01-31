import pytest
from unittest.mock import AsyncMock, MagicMock
from config import Settings, VaultConfig
from app.core.api_client import BaseAPIClient
from app.core.vault_client import VaultClient
from app.services import IllumioService, KubernetesService
from app.models import ContainerCluster, Label, ContainerProfile

@pytest.fixture
def mock_settings():
    """Mock application settings."""
    return Settings(
        environment="testing",
        illumio={
            "base_url": "https://illumio.test",
            "org_id": 1,
            "api_version": "v2"
        },
        secret_key="test-key"
    )

@pytest.fixture
def mock_vault_config():
    """Mock Vault configuration."""
    return VaultConfig(
        url="https://vault.test",
        auth={"method": "token", "token": "test-token"}
    )

@pytest.fixture
def mock_api_client():
    """Mock API client with async methods."""
    client = AsyncMock(spec=BaseAPIClient)
    client.settings = mock_settings()
    return client

@pytest.fixture
def mock_vault_client():
    """Mock Vault client with async methods."""
    client = AsyncMock(spec=VaultClient)
    return client

@pytest.fixture
def mock_k8s_service():
    """Mock Kubernetes service with async methods."""
    service = AsyncMock(spec=KubernetesService)
    return service

@pytest.fixture
def mock_illumio_service(mock_api_client, mock_vault_client):
    """Mock Illumio service with async methods."""
    service = AsyncMock(spec=IllumioService)
    service.api = mock_api_client
    service.vault = mock_vault_client
    return service

@pytest.fixture
def sample_cluster_data():
    """Sample cluster data for testing."""
    return {
        "href": "/orgs/1/container_clusters/123",
        "name": "test-cluster",
        "description": "Test Cluster",
        "enforcement_mode": "visibility_only",
        "online": True,
        "container_cluster_token": "test-token",
        "created_at": "2024-01-31T00:00:00Z",
        "updated_at": "2024-01-31T00:00:00Z",
        "labels": []
    }

@pytest.fixture
def sample_cluster(sample_cluster_data):
    """Sample ContainerCluster instance."""
    return ContainerCluster(**sample_cluster_data)

@pytest.fixture
def sample_label_data():
    """Sample label data for testing."""
    return {
        "href": "/orgs/1/labels/456",
        "key": "env",
        "value": "test",
        "created_at": "2024-01-31T00:00:00Z",
        "updated_at": "2024-01-31T00:00:00Z"
    }

@pytest.fixture
def sample_label(sample_label_data):
    """Sample Label instance."""
    return Label(**sample_label_data)

@pytest.fixture
def sample_profile_data():
    """Sample profile data for testing."""
    return {
        "href": "/orgs/1/container_clusters/123/container_workload_profiles/789",
        "name": "test-profile",
        "namespace": "test-namespace",
        "managed": True,
        "enforcement_mode": "visibility_only",
        "created_at": "2024-01-31T00:00:00Z",
        "updated_at": "2024-01-31T00:00:00Z"
    }

@pytest.fixture
def sample_profile(sample_profile_data):
    """Sample ContainerProfile instance."""
    return ContainerProfile(**sample_profile_data)

@pytest.fixture
def cli_runner():
    """Click CLI test runner."""
    from click.testing import CliRunner
    return CliRunner()

@pytest.fixture(autouse=True)
async def mock_async_context():
    """Provide async context for tests."""
    try:
        yield
    finally:
        # Cleanup any remaining async tasks
        import asyncio
        pending = asyncio.all_tasks()
        for task in pending:
            task.cancel()
