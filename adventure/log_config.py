"""Logging configuration for the adventure game."""

import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(log_file: Optional[str] = None, debug: bool = False) -> logging.Logger:
    """Set up logging configuration.
    
    Args:
        log_file: Optional path to log file. If not provided, logs to stderr
        debug: Whether to enable debug level logging
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger('adventure')
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Create handlers
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # File handler for all levels
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Console handler for INFO and above
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Debug console handler if debug is enabled
    if debug:
        debug_handler = logging.StreamHandler(sys.stderr)
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(console_formatter)
        logger.addHandler(debug_handler)
    
    return logger

def get_logger() -> logging.Logger:
    """Get the configured logger instance.
    
    Returns:
        Logger instance for the adventure game
    """
    return logging.getLogger('adventure') 