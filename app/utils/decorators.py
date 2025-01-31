import functools
import time
import logging
from typing import Any, Callable, TypeVar, cast
from .logger import get_logger
from .exceptions import IllumioClusterManagerError, AuthenticationError

logger = get_logger(__name__)
F = TypeVar('F', bound=Callable[..., Any])

def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0,
         exceptions: tuple = (Exception,)) -> Callable[[F], F]:
    """Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        raise
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed: {str(e)}. "
                        f"Retrying in {current_delay:.1f} seconds..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            if last_exception:
                raise last_exception
        return cast(F, wrapper)
    return decorator

def validate_args(**validators: Callable[[Any], bool]) -> Callable[[F], F]:
    """Validate function arguments using provided validator functions.
    
    Args:
        **validators: Mapping of argument names to their validator functions
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get function's parameter names
            params = func.__code__.co_varnames[:func.__code__.co_argcount]
            
            # Create a mapping of parameter names to their values
            arg_values = dict(zip(params, args))
            arg_values.update(kwargs)
            
            # Validate arguments
            for arg_name, validator in validators.items():
                if arg_name in arg_values:
                    value = arg_values[arg_name]
                    if not validator(value):
                        raise ValueError(f"Invalid value for argument '{arg_name}': {value}")
            
            return func(*args, **kwargs)
        return cast(F, wrapper)
    return decorator

def log_execution(level: str = "DEBUG") -> Callable[[F], F]:
    """Log function execution with timing.
    
    Args:
        level: Logging level to use
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            func_name = func.__name__
            logger.log(getattr(logging, level), f"Executing {func_name}")
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.log(
                    getattr(logging, level),
                    f"Completed {func_name} in {execution_time:.2f} seconds"
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"Failed {func_name} after {execution_time:.2f} seconds: {str(e)}"
                )
                raise
        return cast(F, wrapper)
    return decorator

def require_auth(func: F) -> F:
    """Ensure authentication is present before executing function."""
    @functools.wraps(func)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        if not hasattr(self, 'is_authenticated') or not self.is_authenticated:
            raise AuthenticationError("Authentication required")
        return func(self, *args, **kwargs)
    return cast(F, wrapper)

def deprecated(message: str = "") -> Callable[[F], F]:
    """Mark function as deprecated with optional message."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            warning_message = f"Function {func.__name__} is deprecated."
            if message:
                warning_message += f" {message}"
            logger.warning(warning_message)
            return func(*args, **kwargs)
        return cast(F, wrapper)
    return decorator