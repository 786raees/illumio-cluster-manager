from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from app.core.api_client import BaseAPIClient
from app.core.vault_client import VaultClient
from app.models import (
    Label,
    LabelGroup,
    ContainerProfile,
    ContainerCluster,
    PairingProfile,
    PairingKey,
    Rule,
    ClusterConfig
)
from app.utils import (
    get_logger,
    IllumioRole,
    IllumioEnforcementMode,
    ILLUMIO_ENDPOINTS,
    ILLUMIO_LABEL_TYPES,
    ILLUMIO_DEFAULT_SETTINGS,
    DataHelper,
    ValidationHelper,
    retry,
    log_execution,
    IllumioError,
    ClusterOperationError,
    LabelOperationError
)

class IllumioService:
    """Service for interacting with Illumio PCE."""

    def __init__(self, api_client: BaseAPIClient, vault_client: VaultClient):
        """Initialize Illumio service.
        
        Args:
            api_client: API client for PCE communication
            vault_client: Vault client for secret management
        """
        self.api = api_client
        self.vault = vault_client
        self.logger = get_logger(__name__)
        self.org_id = self.api.settings.org_id

    def _build_url(self, endpoint: str) -> str:
        """Build API URL with proper encoding.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            str: Complete URL
        """
        return f"{self.api.settings.base_url}/orgs/{self.org_id}/{endpoint.strip('/')}"

    @log_execution(level="DEBUG")
    async def get_cluster(self, cluster_name: str) -> Optional[ContainerCluster]:
        """Get cluster by name.
        
        Args:
            cluster_name: Name of the cluster
            
        Returns:
            Optional[ContainerCluster]: Cluster if found, None otherwise
            
        Raises:
            IllumioError: If API request fails
        """
        try:
            clusters = await self.api.request(
                'GET',
                ILLUMIO_ENDPOINTS['container_clusters'],
                params={'name': cluster_name}
            )
            
            for cluster in clusters:
                if cluster['name'] == cluster_name:
                    return ContainerCluster(**cluster)
            return None
            
        except Exception as e:
            raise IllumioError(f"Failed to get cluster {cluster_name}: {str(e)}")

    @log_execution(level="DEBUG")
    async def create_cluster(
        self,
        cluster_name: str,
        description: Optional[str] = None,
        enforcement_mode: IllumioEnforcementMode = IllumioEnforcementMode.VISIBILITY_ONLY
    ) -> ContainerCluster:
        """Create new container cluster.
        
        Args:
            cluster_name: Name of the cluster
            description: Optional cluster description
            enforcement_mode: Enforcement mode
            
        Returns:
            ContainerCluster: Created cluster
            
        Raises:
            ClusterOperationError: If cluster creation fails
        """
        try:
            # Validate cluster name
            if not ValidationHelper.is_valid_cluster_name(cluster_name):
                raise ValueError(f"Invalid cluster name: {cluster_name}")
                
            # Create cluster
            payload = {
                'name': cluster_name,
                'description': description,
                'enforcement_mode': enforcement_mode.value
            }
            
            response = await self.api.request(
                'POST',
                ILLUMIO_ENDPOINTS['container_clusters'],
                data=payload
            )
            
            cluster = ContainerCluster(**response)
            
            # Store cluster info in Vault
            await self._store_cluster_config(cluster)
            
            return cluster
            
        except Exception as e:
            raise ClusterOperationError(f"Failed to create cluster {cluster_name}: {str(e)}")

    async def _store_cluster_config(self, cluster: ContainerCluster) -> None:
        """Store cluster configuration in Vault.
        
        Args:
            cluster: Cluster configuration to store
        """
        config = ClusterConfig(
            cluster_id=cluster.href.split('/')[-1],
            cluster_name=cluster.name,
            cluster_token=cluster.container_cluster_token,
            pairing_key=await self._generate_pairing_key(cluster.name)
        )
        
        await self.vault.store_secret(
            f"clusters/{cluster.name}",
            config.model_dump()
        )

    @log_execution(level="DEBUG")
    async def get_or_create_label(
        self,
        key: str,
        value: str
    ) -> Label:
        """Get existing label or create new one.
        
        Args:
            key: Label key
            value: Label value
            
        Returns:
            Label: Retrieved or created label
            
        Raises:
            LabelOperationError: If label operation fails
        """
        try:
            # Check if label exists
            labels = await self.api.request(
                'GET',
                ILLUMIO_ENDPOINTS['labels'],
                params={'key': key, 'value': value}
            )
            
            if labels:
                return Label(**labels[0])
                
            # Create new label
            payload = {'key': key, 'value': value}
            response = await self.api.request(
                'POST',
                ILLUMIO_ENDPOINTS['labels'],
                data=payload
            )
            
            return Label(**response)
            
        except Exception as e:
            raise LabelOperationError(f"Failed to get/create label {key}={value}: {str(e)}")

    @log_execution(level="DEBUG")
    async def create_namespace_profile(
        self,
        cluster_id: str,
        namespace: str,
        labels: Optional[List[Dict[str, str]]] = None
    ) -> ContainerProfile:
        """Create container workload profile for namespace.
        
        Args:
            cluster_id: Cluster ID
            namespace: Kubernetes namespace
            labels: Optional labels to assign
            
        Returns:
            ContainerProfile: Created profile
            
        Raises:
            IllumioError: If profile creation fails
        """
        try:
            # Validate namespace
            if not ValidationHelper.is_valid_namespace(namespace):
                raise ValueError(f"Invalid namespace: {namespace}")
                
            # Create profile
            payload = {
                'namespace': namespace,
                'managed': True,
                'enforcement_mode': IllumioEnforcementMode.VISIBILITY_ONLY.value
            }
            
            if labels:
                payload['assign_labels'] = labels
                
            response = await self.api.request(
                'POST',
                f"{ILLUMIO_ENDPOINTS['container_clusters']}/{cluster_id}/container_workload_profiles",
                data=payload
            )
            
            return ContainerProfile(**response)
            
        except Exception as e:
            raise IllumioError(f"Failed to create profile for namespace {namespace}: {str(e)}")

    @log_execution(level="DEBUG")
    async def create_intra_namespace_rule(
        self,
        namespace: str,
        cluster_name: str
    ) -> Rule:
        """Create intra-namespace communication rule.
        
        Args:
            namespace: Kubernetes namespace
            cluster_name: Cluster name
            
        Returns:
            Rule: Created rule
            
        Raises:
            IllumioError: If rule creation fails
        """
        try:
            # Get namespace label
            namespace_label = await self.get_or_create_label('namespace', namespace)
            
            # Create rule
            rule = Rule(
                name=f"{cluster_name}-{namespace}-intra-ns",
                enabled=True,
                ingress_services=[{'proto': 6}],  # TCP
                consumers=[{'label': {'href': namespace_label.href}}],
                providers=[{'label': {'href': namespace_label.href}}]
            )
            
            response = await self.api.request(
                'POST',
                ILLUMIO_ENDPOINTS['sec_policy'],
                data=rule.model_dump(exclude_none=True)
            )
            
            return Rule(**response)
            
        except Exception as e:
            raise IllumioError(f"Failed to create intra-namespace rule: {str(e)}")

    async def _generate_pairing_key(self, cluster_name: str) -> str:
        """Generate pairing key for cluster.
        
        Args:
            cluster_name: Cluster name
            
        Returns:
            str: Generated pairing key
        """
        # Create pairing profile
        profile = await self.api.request(
            'POST',
            ILLUMIO_ENDPOINTS['pairing_profiles'],
            data={
                'name': f"{cluster_name}-profile",
                **ILLUMIO_DEFAULT_SETTINGS
            }
        )
        
        # Generate key
        profile_id = profile['href'].split('/')[-1]
        key_response = await self.api.request(
            'POST',
            f"{ILLUMIO_ENDPOINTS['pairing_profiles']}/{profile_id}/pairing_key"
        )
        
        return key_response['activation_code']

    @log_execution(level="DEBUG")
    async def delete_cluster(self, cluster_name: str) -> bool:
        """Delete cluster and associated resources.
        
        Args:
            cluster_name: Name of the cluster
            
        Returns:
            bool: True if successful
            
        Raises:
            ClusterOperationError: If deletion fails
        """
        try:
            cluster = await self.get_cluster(cluster_name)
            if not cluster:
                return False
                
            # Delete cluster
            cluster_id = cluster.href.split('/')[-1]
            await self.api.request(
                'DELETE',
                f"{ILLUMIO_ENDPOINTS['container_clusters']}/{cluster_id}"
            )
            
            # Delete Vault secrets
            await self.vault.delete_secret_versions(f"clusters/{cluster_name}", [])
            
            return True
            
        except Exception as e:
            raise ClusterOperationError(f"Failed to delete cluster {cluster_name}: {str(e)}")

    @log_execution(level="DEBUG")
    async def update_cluster_labels(
        self,
        cluster_name: str,
        labels: List[Dict[str, str]]
    ) -> ContainerCluster:
        """Update cluster labels.
        
        Args:
            cluster_name: Cluster name
            labels: Labels to update
            
        Returns:
            ContainerCluster: Updated cluster
            
        Raises:
            ClusterOperationError: If update fails
        """
        try:
            cluster = await self.get_cluster(cluster_name)
            if not cluster:
                raise ValueError(f"Cluster not found: {cluster_name}")
                
            cluster_id = cluster.href.split('/')[-1]
            response = await self.api.request(
                'PUT',
                f"{ILLUMIO_ENDPOINTS['container_clusters']}/{cluster_id}",
                data={'labels': labels}
            )
            
            return ContainerCluster(**response)
            
        except Exception as e:
            raise ClusterOperationError(f"Failed to update cluster labels: {str(e)}")

    @log_execution(level="DEBUG")
    async def get_cluster_profiles(
        self,
        cluster_id: str
    ) -> List[ContainerProfile]:
        """Get all profiles for a cluster.
        
        Args:
            cluster_id: Cluster ID
            
        Returns:
            List[ContainerProfile]: List of profiles
            
        Raises:
            IllumioError: If retrieval fails
        """
        try:
            response = await self.api.request(
                'GET',
                f"{ILLUMIO_ENDPOINTS['container_clusters']}/{cluster_id}/container_workload_profiles"
            )
            
            return [ContainerProfile(**profile) for profile in response]
            
        except Exception as e:
            raise IllumioError(f"Failed to get cluster profiles: {str(e)}")

    @log_execution(level="DEBUG")
    async def sync_namespace_labels(
        self,
        cluster_id: str,
        namespaces: List[str]
    ) -> None:
        """Sync namespace labels with current namespaces.
        
        Args:
            cluster_id: Cluster ID
            namespaces: List of current namespaces
            
        Raises:
            IllumioError: If sync fails
        """
        try:
            # Get existing profiles
            existing_profiles = await self.get_cluster_profiles(cluster_id)
            existing_namespaces = {
                p.namespace for p in existing_profiles 
                if p.namespace is not None
            }
            
            # Create missing profiles
            for namespace in set(namespaces) - existing_namespaces:
                await self.create_namespace_profile(cluster_id, namespace)
                
        except Exception as e:
            raise IllumioError(f"Failed to sync namespace labels: {str(e)}")