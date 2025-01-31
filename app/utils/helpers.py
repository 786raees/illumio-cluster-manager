from typing import Any, Dict, List, Optional, Union
import re
from urllib.parse import urljoin, urlparse
import json
from datetime import datetime
import hashlib
import ipaddress
from .logger import get_logger
from .constants import PATTERNS, IllumioRole, IllumioEnforcementMode

logger = get_logger(__name__)

class URLHelper:
    """Helper class for URL operations."""
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate if a string is a valid URL.
        
        Args:
            url: URL string to validate
            
        Returns:
            bool: True if valid URL, False otherwise
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception as e:
            logger.debug(f"URL validation failed: {str(e)}")
            return False
    
    @staticmethod
    def join_url(base: str, *parts: str) -> str:
        """Join URL parts safely.
        
        Args:
            base: Base URL
            *parts: Additional URL parts to join
            
        Returns:
            str: Complete URL
        """
        url = base.rstrip('/')
        for part in parts:
            url = urljoin(f"{url}/", part.lstrip('/'))
        return url

class DataHelper:
    """Helper class for data operations."""
    
    @staticmethod
    def safe_get(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
        """Safely get nested dictionary values.
        
        Args:
            data: Dictionary to search in
            *keys: Keys to traverse
            default: Default value if key not found
            
        Returns:
            Any: Value found or default
        """
        try:
            for key in keys:
                data = data[key]
            return data
        except (KeyError, TypeError):
            return default
    
    @staticmethod
    def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries.
        
        Args:
            dict1: First dictionary
            dict2: Second dictionary
            
        Returns:
            Dict: Merged dictionary
        """
        result = dict1.copy()
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = DataHelper.merge_dicts(result[key], value)
            else:
                result[key] = value
        return result

class ValidationHelper:
    """Helper class for data validation."""
    
    @staticmethod
    def is_valid_name(name: str, pattern: str = r'^[a-zA-Z0-9-_]+$') -> bool:
        """Validate if a string matches the required pattern.
        
        Args:
            name: String to validate
            pattern: Regex pattern to match against
            
        Returns:
            bool: True if valid, False otherwise
        """
        return bool(re.match(pattern, name))
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """Sanitize a string by removing special characters.
        
        Args:
            value: String to sanitize
            
        Returns:
            str: Sanitized string
        """
        return re.sub(r'[^a-zA-Z0-9-_]', '', value)
    
    @staticmethod
    def is_valid_cluster_name(name: str) -> bool:
        """Validate cluster name against Illumio requirements."""
        return bool(re.match(PATTERNS['cluster_name'], name))
    
    @staticmethod
    def is_valid_namespace(namespace: str) -> bool:
        """Validate namespace against Kubernetes requirements."""
        return bool(re.match(PATTERNS['namespace'], namespace))
    
    @staticmethod
    def is_valid_label(key: str, value: str) -> bool:
        """Validate Illumio label key and value."""
        return bool(re.match(PATTERNS['label_key'], key) and 
                   re.match(PATTERNS['label_value'], value))
    
    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        """Validate IP address."""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

class HashHelper:
    """Helper class for hashing operations."""
    
    @staticmethod
    def generate_hash(data: Union[str, bytes, Dict, List], algorithm: str = 'sha256') -> str:
        """Generate hash from data.
        
        Args:
            data: Data to hash
            algorithm: Hash algorithm to use
            
        Returns:
            str: Hex digest of hash
        """
        if isinstance(data, (dict, list)):
            data = json.dumps(data, sort_keys=True)
        if isinstance(data, str):
            data = data.encode()
            
        hash_obj = hashlib.new(algorithm)
        hash_obj.update(data)
        return hash_obj.hexdigest()

class TimeHelper:
    """Helper class for time operations."""
    
    @staticmethod
    def get_timestamp(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Get current timestamp in specified format.
        
        Args:
            fmt: DateTime format string
            
        Returns:
            str: Formatted timestamp
        """
        return datetime.now().strftime(fmt)
    
    @staticmethod
    def parse_timestamp(timestamp: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
        """Parse timestamp string to datetime object.
        
        Args:
            timestamp: Timestamp string to parse
            fmt: DateTime format string
            
        Returns:
            Optional[datetime]: Parsed datetime or None if invalid
        """
        try:
            return datetime.strptime(timestamp, fmt)
        except ValueError as e:
            logger.debug(f"Failed to parse timestamp: {str(e)}")
            return None

class IllumioHelper:
    """Helper class for Illumio-specific operations."""
    
    @staticmethod
    def get_role_href(role_name: str, labels: List[Dict[str, Any]]) -> Optional[str]:
        """Get role label href from list of labels."""
        for label in labels:
            if (label.get('key') == 'role' and 
                label.get('value') == role_name):
                return label.get('href')
        return None
    
    @staticmethod
    def build_label_restriction(key: str, hrefs: List[str]) -> Dict[str, Any]:
        """Build label restriction object for Illumio API."""
        return {
            'key': key,
            'restriction': [{'href': href} for href in hrefs]
        }
    
    @staticmethod
    def extract_id_from_href(href: str) -> str:
        """Extract ID from Illumio href."""
        return href.split('/')[-1]
    
    @staticmethod
    def get_enforcement_mode(mode: str) -> str:
        """Get valid enforcement mode."""
        try:
            return IllumioEnforcementMode(mode).value
        except ValueError:
            return IllumioEnforcementMode.VISIBILITY_ONLY.value
