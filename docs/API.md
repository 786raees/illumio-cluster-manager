# Illumio Cluster Manager - API Documentation

## CLI Commands

### Cluster Management

#### Create Cluster
```bash
illumio-cluster-manager create-cluster [OPTIONS] CLUSTER_NAME

Options:
  --namespace TEXT          Kubernetes namespace [default: illumio-system]
  --enforce / --no-enforce  Enable enforcement mode [default: False]
  --verbose                Enable debug logging
  --dry-run               Simulate actions without making changes
  --config TEXT           Path to config file
  --help                  Show this message and exit
```

#### Delete Cluster
```bash
illumio-cluster-manager delete-cluster [OPTIONS] CLUSTER_NAME

Options:
  --verbose               Enable debug logging
  --dry-run              Simulate actions without making changes
  --config TEXT          Path to config file
  --help                 Show this message and exit
```

#### List Clusters
```bash
illumio-cluster-manager list-clusters [OPTIONS]

Options:
  --verbose              Enable debug logging
  --config TEXT         Path to config file
  --help                Show this message and exit
```

#### Get Cluster Details
```bash
illumio-cluster-manager get-cluster [OPTIONS] CLUSTER_NAME

Options:
  --verbose             Enable debug logging
  --config TEXT        Path to config file
  --help               Show this message and exit
```

## Service APIs

### IllumioService

#### Cluster Operations

```python
async def get_cluster(cluster_name: str) -> Optional[ContainerCluster]:
    """Get cluster by name.
    
    Args:
        cluster_name: Name of the cluster
        
    Returns:
        Optional[ContainerCluster]: Cluster if found, None otherwise
        
    Raises:
        IllumioError: If API request fails
    """
```

```python
async def create_cluster(
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
```

```python
async def delete_cluster(cluster_name: str) -> bool:
    """Delete cluster and associated resources.
    
    Args:
        cluster_name: Name of the cluster
        
    Returns:
        bool: True if successful
        
    Raises:
        ClusterOperationError: If deletion fails
    """
```

#### Label Operations

```python
async def get_or_create_label(
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
```

### VaultClient

#### Secret Management

```python
async def store_secret(
    path: str,
    data: Dict[str, Any]
) -> None:
    """Store secret at path.
    
    Args:
        path: Secret path
        data: Secret data
        
    Raises:
        VaultIntegrationError: If storage fails
    """
```

```python
async def get_secret(
    path: str,
    version: Optional[int] = None
) -> Dict[str, Any]:
    """Get secret from path.
    
    Args:
        path: Secret path
        version: Optional version number
        
    Returns:
        Dict[str, Any]: Secret data
        
    Raises:
        VaultIntegrationError: If retrieval fails
    """
```

### KubernetesService

#### Resource Management

```python
async def create_namespace(
    name: str = K8S_NAMESPACE
) -> None:
    """Create Kubernetes namespace.
    
    Args:
        name: Namespace name
        
    Raises:
        KubernetesError: If namespace creation fails
    """
```

```python
async def create_service_account(
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
```

## Models

### ContainerCluster
```python
class ContainerCluster(BaseModel):
    href: str
    name: str
    description: Optional[str]
    enforcement_mode: str
    online: bool
    container_cluster_token: Optional[str]
    created_at: datetime
    updated_at: datetime
    labels: List[Dict[str, str]] = []
```

### Label
```python
class Label(BaseModel):
    href: str
    key: str
    value: str
    created_at: datetime
    updated_at: datetime
```

### ContainerProfile
```python
class ContainerProfile(BaseModel):
    href: str
    name: str
    namespace: str
    managed: bool
    enforcement_mode: str
    created_at: datetime
    updated_at: datetime
```

## Error Handling

### Exception Hierarchy
```
BaseException
└── Exception
    └── IllumioManagerError
        ├── IllumioError
        │   ├── ClusterOperationError
        │   └── LabelOperationError
        ├── VaultError
        │   ├── VaultIntegrationError
        │   └── VaultAuthenticationError
        └── KubernetesError
```

## Configuration

See `.env` file for all available configuration options and their descriptions.
