import logging
import sys
from typing import Optional
from logging.handlers import RotatingFileHandler
import os
from rich.logging import RichHandler

class LoggerConfig:
    """Configure application logging with both file and console output."""
    
    def __init__(
        self,
        log_level: str = "INFO",
        log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        log_file: Optional[str] = None,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        use_rich_logging: bool = True
    ):
        """Initialize logger configuration.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_format: Format string for log messages
            log_file: Optional file path for logging to file
            max_bytes: Maximum size of log file before rotation
            backup_count: Number of backup files to keep
            use_rich_logging: Whether to use Rich for console logging
        """
        self.log_level = getattr(logging, log_level.upper())
        self.log_format = log_format
        self.log_file = log_file
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.use_rich_logging = use_rich_logging
        
    def setup(self) -> None:
        """Set up logging configuration."""
        # Create formatter
        formatter = logging.Formatter(self.log_format)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # Clear any existing handlers
        root_logger.handlers = []
        
        # Add console handler with Rich formatting if enabled
        if self.use_rich_logging:
            console_handler = RichHandler(
                rich_tracebacks=True,
                markup=True,
                show_time=True,
                show_path=True
            )
        else:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            
        root_logger.addHandler(console_handler)
        
        # Add file handler if log file is specified
        if self.log_file:
            try:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
                
                file_handler = RotatingFileHandler(
                    self.log_file,
                    maxBytes=self.max_bytes,
                    backupCount=self.backup_count
                )
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)
            except Exception as e:
                root_logger.error(f"Failed to set up file logging: {str(e)}")

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name.
    
    Args:
        name: Name for the logger, typically __name__ of the module
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)
