"""
Comprehensive logging configuration for Warcry data processing.

Provides structured logging with configurable levels, formats and outputs.
"""

import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import PROJECT_ROOT


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging output."""
    
    def __init__(self, include_process_info: bool = False):
        """Initialize the formatter.
        
        Args:
            include_process_info: Whether to include process/thread information
        """
        self.include_process_info = include_process_info
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with structured information."""
        # Create base log entry
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add location information for warnings and errors
        if record.levelno >= logging.WARNING:
            log_entry.update({
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno,
            })
        
        # Add process information if requested
        if self.include_process_info:
            log_entry.update({
                'process': record.process,
                'thread': record.thread,
            })
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Format as readable string
        parts = [f"{log_entry['timestamp']} - {log_entry['level']} - {log_entry['logger']}"]
        
        if 'module' in log_entry:
            parts.append(f"({log_entry['module']}.{log_entry['function']}:{log_entry['line']})")
        
        parts.append(f"- {log_entry['message']}")
        
        if 'exception' in log_entry:
            parts.append(f"\n{log_entry['exception']}")
        
        return " ".join(parts)


class WarcryLogger:
    """Centralized logging configuration for Warcry data processing."""
    
    _instance: Optional['WarcryLogger'] = None
    _configured: bool = False
    
    def __new__(cls) -> 'WarcryLogger':
        """Singleton pattern to ensure single logging configuration."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the logger configuration."""
        if not self._configured:
            self.setup_logging()
            self._configured = True
    
    def setup_logging(self, 
                     level: str = "INFO",
                     log_file: Optional[Path] = None,
                     include_console: bool = True,
                     include_process_info: bool = False,
                     max_file_size: int = 10 * 1024 * 1024,  # 10MB
                     backup_count: int = 5) -> None:
        """Configure comprehensive logging for the application.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional file path for log output
            include_console: Whether to include console output
            include_process_info: Whether to include process/thread info
            max_file_size: Maximum log file size before rotation
            backup_count: Number of backup files to keep
        """
        # Create formatter
        formatter = StructuredFormatter(include_process_info=include_process_info)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, level.upper()))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        handlers = []
        
        # Console handler
        if include_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(getattr(logging, level.upper()))
            handlers.append(console_handler)
        
        # File handler with rotation
        if log_file:
            log_file = Path(log_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_file,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(getattr(logging, level.upper()))
            handlers.append(file_handler)
        
        # Add all handlers to root logger
        for handler in handlers:
            root_logger.addHandler(handler)
        
        # Set up module-specific loggers
        self._configure_module_loggers()
        
        # Log configuration success
        logging.info(f"Logging configured - Level: {level}, Handlers: {len(handlers)}")
        if log_file:
            logging.info(f"Log file: {log_file}")
    
    def _configure_module_loggers(self) -> None:
        """Configure module-specific logger settings."""
        # Warcry data processing modules
        warcry_logger = logging.getLogger('python.data_parsing')
        warcry_logger.setLevel(logging.INFO)
        
        # Reduce verbosity of external libraries
        logging.getLogger('jsonschema').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        
        # Set validation logger to be more verbose
        logging.getLogger('python.data_parsing.validation_system').setLevel(logging.DEBUG)
    
    def get_performance_logger(self) -> logging.Logger:
        """Get a logger specifically for performance monitoring."""
        logger = logging.getLogger('python.data_parsing.performance')
        return logger
    
    def get_validation_logger(self) -> logging.Logger:
        """Get a logger specifically for validation operations."""
        logger = logging.getLogger('python.data_parsing.validation')
        return logger
    
    def get_export_logger(self) -> logging.Logger:
        """Get a logger specifically for export operations."""
        logger = logging.getLogger('python.data_parsing.export')
        return logger


class PerformanceTimer:
    """Context manager for timing operations with automatic logging."""
    
    def __init__(self, operation_name: str, logger: Optional[logging.Logger] = None):
        """Initialize the timer.
        
        Args:
            operation_name: Name of the operation being timed
            logger: Logger to use (defaults to performance logger)
        """
        self.operation_name = operation_name
        self.logger = logger or WarcryLogger().get_performance_logger()
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def __enter__(self) -> 'PerformanceTimer':
        """Start timing the operation."""
        import time
        self.start_time = time.perf_counter()
        self.logger.info(f"Starting {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Stop timing and log the duration."""
        import time
        self.end_time = time.perf_counter()
        duration = self.end_time - self.start_time
        
        if exc_type is None:
            self.logger.info(f"Completed {self.operation_name} in {duration:.3f} seconds")
        else:
            self.logger.error(f"Failed {self.operation_name} after {duration:.3f} seconds: {exc_val}")
    
    @property
    def duration(self) -> Optional[float]:
        """Get the duration of the operation."""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


def setup_default_logging(debug: bool = False) -> None:
    """Setup default logging configuration for the application.
    
    Args:
        debug: Whether to enable debug-level logging
    """
    level = "DEBUG" if debug else "INFO"
    log_file = PROJECT_ROOT / "logs" / f"warcry_data_{datetime.now().strftime('%Y%m%d')}.log"
    
    logger = WarcryLogger()
    logger.setup_logging(
        level=level,
        log_file=log_file,
        include_console=True,
        include_process_info=debug
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    # Ensure logging is configured
    WarcryLogger()
    return logging.getLogger(name)


# Convenience functions for specific logger types
def get_performance_logger() -> logging.Logger:
    """Get the performance logger."""
    return WarcryLogger().get_performance_logger()


def get_validation_logger() -> logging.Logger:
    """Get the validation logger."""
    return WarcryLogger().get_validation_logger()


def get_export_logger() -> logging.Logger:
    """Get the export logger."""
    return WarcryLogger().get_export_logger()
