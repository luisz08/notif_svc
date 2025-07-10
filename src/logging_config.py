"""
Logging configuration module for the notification service.
"""

import logging
import logging.handlers
import sys
import json
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from .config import LoggingConfig


class DetailedFormatter(logging.Formatter):
    """Detailed formatter for development environment."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color support for different log levels
        colors = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',    # Red
            'CRITICAL': '\033[35m', # Magenta
        }
        reset_color = '\033[0m'
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Get color for log level
        color = colors.get(record.levelname, '')
        
        # Format the message
        formatted_message = (
            f"{timestamp} | "
            f"{color}{record.levelname:<8}{reset_color} | "
            f"{record.name}:{record.lineno} | "
            f"{record.getMessage()}"
        )
        
        # Add exception info if present
        if record.exc_info:
            formatted_message += "\n" + self.formatException(record.exc_info)
        
        return formatted_message


class SimpleFormatter(logging.Formatter):
    """Simple formatter for production environment."""
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        formatted_message = (
            f"{timestamp} | {record.levelname:<5} | {record.getMessage()}"
        )
        
        if record.exc_info:
            formatted_message += "\n" + self.formatException(record.exc_info)
        
        return formatted_message


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = getattr(record, 'request_id', None)
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = getattr(record, 'user_id', None)
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(config: LoggingConfig) -> None:
    """Setup logging configuration based on the provided config."""
    
    # Get root logger
    root_logger = logging.getLogger()
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set log level
    log_level = getattr(logging, config.level.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    
    # Choose formatter based on format type
    formatter_map = {
        'detailed': DetailedFormatter(),
        'simple': SimpleFormatter(),
        'json': JsonFormatter(),
    }
    formatter = formatter_map.get(config.format, DetailedFormatter())
    
    # Setup console handler if enabled
    if config.console_enabled:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        root_logger.addHandler(console_handler)
    
    # Setup file handler if enabled
    if config.file_enabled and config.file_path:
        file_path = Path(config.file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use rotating file handler to prevent log files from growing too large
        file_handler = logging.handlers.RotatingFileHandler(
            filename=config.file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    configure_loggers(log_level)


def configure_loggers(log_level: int) -> None:
    """Configure specific loggers with appropriate levels."""
    
    # Set uvicorn loggers to a higher level to reduce noise
    logging.getLogger("uvicorn").setLevel(max(log_level, logging.INFO))
    logging.getLogger("uvicorn.access").setLevel(max(log_level, logging.INFO))
    
    # Set SQLAlchemy loggers
    logging.getLogger("sqlalchemy.engine").setLevel(max(log_level, logging.WARNING))
    logging.getLogger("sqlalchemy.pool").setLevel(max(log_level, logging.WARNING))
    
    # Set httpx/requests loggers
    logging.getLogger("httpx").setLevel(max(log_level, logging.WARNING))
    logging.getLogger("requests").setLevel(max(log_level, logging.WARNING))


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger instance for this class."""
        return logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")


# Convenience function to create logger with extra context
def get_logger_with_context(**context) -> logging.LoggerAdapter:
    """Get a logger adapter with additional context."""
    logger = logging.getLogger()
    return logging.LoggerAdapter(logger, context)
