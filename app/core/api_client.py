import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, Dict, Any, Union
from app.models.config import Settings
from app.utils import (
    get_logger,
    URLHelper,
    DataHelper,
    HTTPMethod,
    DEFAULT_HEADERS,
    DEFAULT_API_TIMEOUT,
    APIError,
    APIConnectionError,
    AuthenticationError,
    retry,
    log_execution
)

class BaseAPIClient:
    """Base API client with retry logic and error handling."""

    def __init__(self, settings: Settings):
        """Initialize API client.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.logger = get_logger(__name__)
        self.session = self._create_session()
        self.base_url = str(settings.base_url).rstrip('/')
        
    def _create_session(self) -> requests.Session:
        """Create configured session with retry logic.
        
        Returns:
            requests.Session: Configured session
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.settings.max_retries,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=frozenset(['GET', 'POST', 'PUT', 'DELETE', 'PATCH']),
            raise_on_status=True
        )
        
        # Add retry adapter to session
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        
        return session

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and errors.
        
        Args:
            response: Response from API
            
        Returns:
            Dict[str, Any]: Parsed response data
            
        Raises:
            AuthenticationError: If authentication fails
            APIError: If API request fails
            APIConnectionError: If response parsing fails
        """
        try:
            response.raise_for_status()
            
            if not response.content:
                return {}
                
            try:
                return response.json()
            except json.JSONDecodeError as e:
                raise APIConnectionError(f"Invalid JSON response: {str(e)}")
                
        except requests.exceptions.HTTPError as e:
            error_data = {}
            try:
                error_data = response.json()
            except (json.JSONDecodeError, AttributeError):
                error_data = {'raw_response': response.text}
                
            if response.status_code == 401:
                raise AuthenticationError(
                    message="Authentication failed",
                    status_code=response.status_code,
                    response=error_data
                )
                
            raise APIError(
                message=f"API request failed: {str(e)}",
                status_code=response.status_code,
                response=error_data
            )

    @retry(max_attempts=3, exceptions=(APIConnectionError,))
    @log_execution(level="DEBUG")
    def request(
        self,
        method: Union[str, HTTPMethod],
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Make API request with enhanced security and logging.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body
            headers: Request headers
            timeout: Request timeout
            
        Returns:
            Dict[str, Any]: Response data
            
        Raises:
            APIConnectionError: If network error occurs
            APIError: If API request fails
            AuthenticationError: If authentication fails
        """
        # Normalize method
        if isinstance(method, HTTPMethod):
            method = method.value
        method = method.upper()
        
        # Build URL
        url = URLHelper.join_url(self.base_url, endpoint)
        
        # Prepare headers
        request_headers = DEFAULT_HEADERS.copy()
        if headers:
            request_headers.update(headers)
            
        # Add authentication if available
        if hasattr(self.settings, 'api_key'):
            request_headers['Authorization'] = f"Bearer {self.settings.api_key}"
            
        # Set timeout
        timeout = timeout or DEFAULT_API_TIMEOUT
        
        try:
            self.logger.debug(
                f"Making {method} request to {url}",
                extra={
                    'params': params,
                    'headers': {k: v for k, v in request_headers.items() 
                              if k.lower() != 'authorization'}
                }
            )
            
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                headers=request_headers,
                verify=self.settings.verify_ssl,
                timeout=timeout
            )
            
            return self._handle_response(response)
            
        except requests.exceptions.RequestException as e:
            raise APIConnectionError(f"Network error: {str(e)}")
            
    def close(self) -> None:
        """Close the session."""
        self.session.close()