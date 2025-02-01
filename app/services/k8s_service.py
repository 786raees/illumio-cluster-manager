import subprocess
from typing import Optional, List, Dict, Any
from app.core.exceptions import IllumioManagerError
from app.models.config import Settings
import logging
import tempfile
import yaml
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from app.utils import (
    get_logger,
    K8S_NAMESPACE,
    K8S_SERVICE_ACCOUNT,
    K8S_CONFIG_MAP,
    K8S_SECRET,
    retry,
    log_execution,
    KubernetesError,
    ValidationHelper
)

class KubernetesService:
    """Service for managing Kubernetes operations."""

    def __init__(self, kube_config_path: Optional[str] = None):
        """Initialize Kubernetes service.
        
        Args:
            kube_config_path: Optional path to kubeconfig file
        """
        self.logger = get_logger(__name__)
        self._load_config(kube_config_path)
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.rbac_v1 = client.RbacAuthorizationV1Api()

    def _load_config(self, kube_config_path: Optional[str] = None) -> None:
        """Load Kubernetes configuration.
        
        Args:
            kube_config_path: Optional path to kubeconfig file
            
        Raises:
            KubernetesError: If config loading fails
        """
        try:
            if kube_config_path:
                config.load_kube_config(kube_config_path)
            else:
                config.load_incluster_config()
        except Exception as e:
            raise KubernetesError(f"Failed to load Kubernetes config: {str(e)}")

    # @log_execution(level="DEBUG")
    # @retry(max_attempts=3)
    # async def create_namespace(self, name: str = K8S_NAMESPACE) -> None:
    #     """Create Kubernetes namespace.
        
    #     Args:
    #         name: Namespace name
            
    #     Raises:
    #         KubernetesError: If namespace creation fails
    #     """
    #     try:
    #         if not ValidationHelper.is_valid_namespace(name):
    #             raise ValueError(f"Invalid namespace name: {name}")
                
    #         namespace = client.V1Namespace(
    #             metadata=client.V1ObjectMeta(name=name)
    #         )
            
    #         self.core_v1.create_namespace(namespace)
    #         self.logger.info(f"Created namespace: {name}")
            
    #     except ApiException as e:
    #         if e.status == 409:  # Already exists
    #             self.logger.debug(f"Namespace {name} already exists")
    #         else:
    #             raise KubernetesError(f"Failed to create namespace: {str(e)}")
    #     except Exception as e:
    #         raise KubernetesError(f"Failed to create namespace: {str(e)}")

    @log_execution(level="DEBUG")
    @retry(max_attempts=3)
    async def create_service_account(
        self,
        name: str = K8S_SERVICE_ACCOUNT,
        namespace: str = K8S_NAMESPACE
    ) -> None:
        """Create service account.
        
        Args:
            name: Service account name
            namespace: Namespace name
            
        Raises:
            KubernetesError: If service account creation fails
        """
        try:
            service_account = client.V1ServiceAccount(
                metadata=client.V1ObjectMeta(
                    name=name,
                    namespace=namespace
                )
            )
            
            self.core_v1.create_namespaced_service_account(
                namespace=namespace,
                body=service_account
            )
            self.logger.info(f"Created service account: {name}")
            
        except ApiException as e:
            if e.status == 409:  # Already exists
                self.logger.debug(f"Service account {name} already exists")
            else:
                raise KubernetesError(f"Failed to create service account: {str(e)}")
        except Exception as e:
            raise KubernetesError(f"Failed to create service account: {str(e)}")

    @log_execution(level="DEBUG")
    @retry(max_attempts=3)
    async def create_config_map(
        self,
        name: str = K8S_CONFIG_MAP,
        namespace: str = K8S_NAMESPACE,
        data: Dict[str, str] = None
    ) -> None:
        """Create config map.
        
        Args:
            name: Config map name
            namespace: Namespace name
            data: Config map data
            
        Raises:
            KubernetesError: If config map creation fails
        """
        try:
            config_map = client.V1ConfigMap(
                metadata=client.V1ObjectMeta(
                    name=name,
                    namespace=namespace
                ),
                data=data or {}
            )
            
            self.core_v1.create_namespaced_config_map(
                namespace=namespace,
                body=config_map
            )
            self.logger.info(f"Created config map: {name}")
            
        except ApiException as e:
            if e.status == 409:  # Already exists
                self.logger.debug(f"Config map {name} already exists")
            else:
                raise KubernetesError(f"Failed to create config map: {str(e)}")
        except Exception as e:
            raise KubernetesError(f"Failed to create config map: {str(e)}")

    @log_execution(level="DEBUG")
    @retry(max_attempts=3)
    async def create_secret(
        self,
        name: str = K8S_SECRET,
        namespace: str = K8S_NAMESPACE,
        data: Dict[str, str] = None
    ) -> None:
        """Create secret.
        
        Args:
            name: Secret name
            namespace: Namespace name
            data: Secret data
            
        Raises:
            KubernetesError: If secret creation fails
        """
        try:
            # Encode secret data
            encoded_data = {
                k: self._encode_secret(v)
                for k, v in (data or {}).items()
            }
            
            secret = client.V1Secret(
                metadata=client.V1ObjectMeta(
                    name=name,
                    namespace=namespace
                ),
                type="Opaque",
                data=encoded_data
            )
            
            self.core_v1.create_namespaced_secret(
                namespace=namespace,
                body=secret
            )
            self.logger.info(f"Created secret: {name}")
            
        except ApiException as e:
            if e.status == 409:  # Already exists
                self.logger.debug(f"Secret {name} already exists")
            else:
                raise KubernetesError(f"Failed to create secret: {str(e)}")
        except Exception as e:
            raise KubernetesError(f"Failed to create secret: {str(e)}")

    @staticmethod
    def _encode_secret(value: str) -> str:
        """Encode secret value in base64.
        
        Args:
            value: Value to encode
            
        Returns:
            str: Base64 encoded value
        """
        import base64
        return base64.b64encode(value.encode()).decode()

    @log_execution(level="DEBUG")
    async def list_namespaces(self) -> List[str]:
        """List all namespaces.
        
        Returns:
            List[str]: List of namespace names
            
        Raises:
            KubernetesError: If listing fails
        """
        try:
            namespaces = self.core_v1.list_namespace()
            return [ns.metadata.name for ns in namespaces.items]
        except Exception as e:
            raise KubernetesError(f"Failed to list namespaces: {str(e)}")

    @log_execution(level="DEBUG")
    async def delete_namespace(self, name: str) -> None:
        """Delete namespace.
        
        Args:
            name: Namespace name
            
        Raises:
            KubernetesError: If deletion fails
        """
        try:
            self.core_v1.delete_namespace(name)
            self.logger.info(f"Deleted namespace: {name}")
        except ApiException as e:
            if e.status == 404:  # Not found
                self.logger.debug(f"Namespace {name} not found")
            else:
                raise KubernetesError(f"Failed to delete namespace: {str(e)}")
        except Exception as e:
            raise KubernetesError(f"Failed to delete namespace: {str(e)}")

    @log_execution(level="DEBUG")
    async def check_namespace_exists(self, name: str) -> bool:
        """Check if namespace exists.
        
        Args:
            name: Namespace name
            
        Returns:
            bool: True if exists, False otherwise
        """
        try:
            self.core_v1.read_namespace(name)
            return True
        except ApiException as e:
            if e.status == 404:
                return False
            raise KubernetesError(f"Failed to check namespace: {str(e)}")
        except Exception as e:
            raise KubernetesError(f"Failed to check namespace: {str(e)}")

    @log_execution(level="DEBUG")
    async def get_pod_logs(
        self,
        name: str,
        namespace: str = K8S_NAMESPACE,
        container: Optional[str] = None,
        tail_lines: Optional[int] = None
    ) -> str:
        """Get pod logs.
        
        Args:
            name: Pod name
            namespace: Namespace name
            container: Container name
            tail_lines: Number of lines to return
            
        Returns:
            str: Pod logs
            
        Raises:
            KubernetesError: If log retrieval fails
        """
        try:
            return self.core_v1.read_namespaced_pod_log(
                name=name,
                namespace=namespace,
                container=container,
                tail_lines=tail_lines
            )
        except Exception as e:
            raise KubernetesError(f"Failed to get pod logs: {str(e)}")

    @log_execution(level="DEBUG")
    async def get_pod_status(
        self,
        name: str,
        namespace: str = K8S_NAMESPACE
    ) -> Dict[str, Any]:
        """Get pod status.
        
        Args:
            name: Pod name
            namespace: Namespace name
            
        Returns:
            Dict[str, Any]: Pod status
            
        Raises:
            KubernetesError: If status retrieval fails
        """
        try:
            pod = self.core_v1.read_namespaced_pod_status(
                name=name,
                namespace=namespace
            )
            return {
                'phase': pod.status.phase,
                'conditions': [
                    {
                        'type': c.type,
                        'status': c.status,
                        'message': c.message
                    }
                    for c in (pod.status.conditions or [])
                ],
                'container_statuses': [
                    {
                        'name': c.name,
                        'ready': c.ready,
                        'state': str(c.state)
                    }
                    for c in (pod.status.container_statuses or [])
                ]
            }
        except Exception as e:
            raise KubernetesError(f"Failed to get pod status: {str(e)}")

    @log_execution(level="DEBUG")
    async def wait_for_pod_ready(
        self,
        name: str,
        namespace: str = K8S_NAMESPACE,
        timeout: int = 300
    ) -> bool:
        """Wait for pod to be ready.
        
        Args:
            name: Pod name
            namespace: Namespace name
            timeout: Timeout in seconds
            
        Returns:
            bool: True if ready, False if timeout
            
        Raises:
            KubernetesError: If status check fails
        """
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                status = await self.get_pod_status(name, namespace)
                if status['phase'] == 'Running' and all(
                    c['ready'] for c in status['container_statuses']
                ):
                    return True
                    
                time.sleep(5)
                
            except Exception as e:
                self.logger.warning(f"Error checking pod status: {str(e)}")
                time.sleep(5)
                
        return False

    # def create_namespace(self) -> bool:
    #     """Create Kubernetes namespace with validation"""
    #     try:
    #         cmd = f"kubectl create ns {self.namespace} --dry-run=client -o yaml | kubectl apply -f -"
    #         result = subprocess.run(
    #             cmd,
    #             shell=True,
    #             check=True,
    #             capture_output=True,
    #             text=True
    #         )
    #         self.logger.info(f"Namespace created: {result.stdout}")
    #         return True
    #     except subprocess.CalledProcessError as e:
    #         self.logger.error(f"Namespace creation failed: {e.stderr}")
    #         raise IllumioManagerError("Kubernetes namespace setup failed")

    # def install_helm_chart(self, cluster_id: str, cluster_token: str, pairing_key: str) -> bool:
    #     """Install Helm chart with secret values"""
    #     try:
    #         # Create temporary values file
    #         with tempfile.NamedTemporaryFile(mode='w', delete=True) as values_file:
    #             values = {
    #                 'cluster_id': cluster_id,
    #                 'cluster_token': cluster_token,
    #                 'cluster_code': pairing_key,
    #                 'controller': {
    #                     'logLevel': 'debug' if self.settings.environment != 'prod' else 'info'
    #                 }
    #             }
    #             yaml.dump(values, values_file)
                
    #             cmd = (
    #                 f"helm upgrade --install illumio "
    #                 f"--namespace {self.namespace} "
    #                 f"--values {values_file.name} "
    #                 f"./helm-charts/illumio"
    #             )
                
    #             result = subprocess.run(
    #                 cmd,
    #                 shell=True,
    #                 check=True,
    #                 capture_output=True,
    #                 text=True
    #             )
    #             self.logger.info(f"Helm install output: {result.stdout}")
    #             return True
    #     except (subprocess.CalledProcessError, yaml.YAMLError) as e:
    #         self.logger.error(f"Helm installation failed: {str(e)}")
    #         raise IllumioManagerError("Helm chart deployment failed")

    def apply_namespace_labels(self, cluster_name: str) -> bool:
        """Apply namespace labels from original workflow"""
        try:
            # Preserve original label logic with improved safety
            cmd = (
                f"kubectl label ns {self.namespace} "
                f"environment={self._get_env_label(cluster_name)} "
                f"location={self._get_location_label(cluster_name)} "
                f"cluster={cluster_name} --overwrite"
            )
            result = subprocess.run(
                cmd,
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Label application failed: {e.stderr}")
            raise IllumioManagerError("Namespace labeling failed")

    def _get_env_label(self, cluster_name: str) -> str:
        """Preserve original environment detection logic"""
        env_map = {
            'dv': 'Development',
            'te': 'Clone',
            'st': 'Clone',
            'pr': 'Production'
        }
        return env_map.get(cluster_name[8:10], 'Development')

    def _get_location_label(self, cluster_name: str) -> str:
        """Preserve original location detection logic"""
        location_map = {
            's': 'Azure South Central US',
            'n': 'Azure North Central US',
            'g': 'Azure Greenfield'
        }
        return location_map.get(cluster_name[6:7], 'Azure Central US')
