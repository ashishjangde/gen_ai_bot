import logging
import sys
from typing import Any
from app.config.settings import settings


class CustomFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    grey = "\x1b[38;20m"
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    format_str = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    
    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: green + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset,
    }
    
    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno, self.format_str)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


class JSONFormatter(logging.Formatter):
    """JSON formatter for production (structured logging)"""
    
    def format(self, record: logging.LogRecord) -> str:
        import json
        from datetime import datetime
        
        log_record: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, "extra"):
            log_record["extra"] = record.extra
        
        return json.dumps(log_record)


def setup_logging() -> None:
    """Configure logging for the application"""
    
    # Determine log level from settings
    log_level = logging.DEBUG if settings.debug else logging.INFO
    
    # Configure app logger (not root to avoid uvicorn duplicates)
    app_root = logging.getLogger("app")
    app_root.setLevel(log_level)
    app_root.handlers.clear()
    app_root.propagate = False  # Don't propagate to root
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Use colored formatter in dev, JSON in production
    if settings.env == "production":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(CustomFormatter())
    
    app_root.addHandler(console_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)


# Pre-configured loggers for common modules
app_logger = get_logger("app")
auth_logger = get_logger("app.auth")
chat_logger = get_logger("app.chat")
db_logger = get_logger("app.db")
