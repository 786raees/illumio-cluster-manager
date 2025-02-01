from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from app.utils import ValidationHelper
from app.utils.constants import IllumioEnforcementMode

class Label(BaseModel):
    """Illumio label model."""
    key: str
    value: str
    href: Optional[str] = None
    
    @field_validator('key', 'value')
    @classmethod
    def validate_label_format(cls, v: str, info: Dict[str, Any]) -> str:
        """Validate label key and value format."""
        field_name = info.field_name
        if not ValidationHelper.is_valid_label(v, v):
            raise ValueError(f"Invalid {field_name} format: {v}")
        return v

class LabelGroup(BaseModel):
    """Illumio label group model."""
    name: str
    description: Optional[str] = None
    labels: List[Label] = Field(default_factory=list)
    href: Optional[str] = None

class Restriction(BaseModel):
    """Label restriction model."""
    key: str
    restriction: List[Dict[str, str]]

class ContainerProfile(BaseModel):
    """Container workload profile model."""
    name: str
    description: Optional[str] = None
    namespace: Optional[str] = None
    managed: bool = True
    enforcement_mode: IllumioEnforcementMode = IllumioEnforcementMode.VISIBILITY_ONLY
    visibility_level: str = "flow_summary"
    labels: List[Restriction] = Field(default_factory=list)
    assign_labels: List[Dict[str, str]] = Field(default_factory=list)
    href: Optional[str] = None
    
    @field_validator('namespace')
    @classmethod
    def validate_namespace(cls, v: Optional[str]) -> Optional[str]:
        """Validate namespace format if provided."""
        if v is not None and not ValidationHelper.is_valid_namespace(v):
            raise ValueError(f"Invalid namespace format: {v}")
        return v

class ContainerCluster(BaseModel):
    """Container cluster model."""
    name: str
    description: Optional[str] = None
    container_cluster_token: Optional[str] = None
    enforcement_mode: IllumioEnforcementMode = IllumioEnforcementMode.VISIBILITY_ONLY
    container_runtime: str = "kubernetes"
    manager_type: str = "kubernetes"
    online: bool = True
    href: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @field_validator('name')
    @classmethod
    def validate_cluster_name(cls, v: str) -> str:
        """Validate cluster name format."""
        if not ValidationHelper.is_valid_cluster_name(v):
            raise ValueError(f"Invalid cluster name format: {v}")
        return v

class PairingProfile(BaseModel):
    """Pairing profile model."""
    name: str
    enabled: bool = True
    enforcement_mode: IllumioEnforcementMode = IllumioEnforcementMode.VISIBILITY_ONLY
    visibility_level: str = "flow_summary"
    allowed_uses_per_key: str = "unlimited"
    key_lifespan: str = "unlimited"
    role_label_lock: bool = True
    app_label_lock: bool = True
    env_label_lock: bool = True
    loc_label_lock: bool = True
    enforcement_mode_lock: bool = True
    log_traffic: bool = False
    log_traffic_lock: bool = True
    labels: List[Dict[str, str]] = Field(default_factory=list)
    href: Optional[str] = None

class PairingKey(BaseModel):
    """Pairing key model."""
    activation_code: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    href: Optional[str] = None

class Rule(BaseModel):
    """Security policy rule model."""
    name: str
    enabled: bool = True
    description: Optional[str] = None
    ingress_services: List[Dict[str, Any]] = Field(default_factory=list)
    resolve_labels_as: Dict[str, str] = Field(default_factory=dict)
    consumers: List[Dict[str, Any]] = Field(default_factory=list)
    providers: List[Dict[str, Any]] = Field(default_factory=list)
    href: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_rule_components(self) -> 'Rule':
        """Validate rule has required components."""
        if not self.ingress_services:
            raise ValueError("Rule must have at least one ingress service")
        if not self.consumers or not self.providers:
            raise ValueError("Rule must have both consumers and providers")
        return self

class ClusterConfig(BaseModel):
    """Cluster configuration model."""
    cluster_id: str
    cluster_name: str
    cluster_token: str
    pairing_key: str
    namespace: str = "illumio-system"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator('cluster_name', 'namespace')
    @classmethod
    def validate_names(cls, v: str, info: Dict[str, Any]) -> str:
        """Validate cluster name and namespace formats."""
        field_name = info.field_name
        if field_name == 'cluster_name':
            if not ValidationHelper.is_valid_cluster_name(v):
                raise ValueError(f"Invalid cluster name format: {v}")
        elif field_name == 'namespace':
            if not ValidationHelper.is_valid_namespace(v):
                raise ValueError(f"Invalid namespace format: {v}")
        return v
