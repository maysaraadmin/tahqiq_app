"""
Centralized error handling utilities for the Tahqiq application.
Provides consistent error handling across the application.
"""

import logging
from functools import wraps
from typing import Any, Callable, Optional
from PyQt6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)

class ErrorContext:
    """Context for error information"""
    def __init__(self, operation: str, user_message: str = None):
        self.operation = operation
        self.user_message = user_message
        self.timestamp = None

def handle_exceptions(
    default_return: Any = None,
    error_message: str = "Operation failed",
    show_user_message: bool = True,
    log_error: bool = True
):
    """
    Decorator for standardized exception handling
    
    Args:
        default_return: Value to return on error
        error_message: Error message to log
        show_user_message: Whether to show message to user
        log_error: Whether to log the error
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = ErrorContext(func.__name__)
                
                if log_error:
                    logger.error(f"{error_message}: {e}", exc_info=True)
                
                if show_user_message and args and hasattr(args[0], 'parent'):  # Check if first arg has parent (QWidget)
                    try:
                        QMessageBox.critical(
                            args[0].parent() if hasattr(args[0], 'parent') else args[0],
                            "Error",
                            f"{error_message}: {str(e)}"
                        )
                    except:
                        logger.error("Failed to show error message to user")
                
                return default_return
        return wrapper
    return decorator

def safe_execute(
    func: Callable,
    default_return: Any = None,
    error_message: str = "Operation failed",
    log_error: bool = True
) -> Any:
    """
    Safely execute a function with standardized error handling
    
    Args:
        func: Function to execute
        default_return: Value to return on error
        error_message: Error message to log
        log_error: Whether to log errors
    """
    try:
        return func()
    except Exception as e:
        if log_error:
            logger.error(f"{error_message}: {e}", exc_info=True)
        return default_return

def log_exception(
    operation: str,
    error: Exception,
    user_message: str = None
):
    """
    Log an exception with context information
    
    Args:
        operation: Operation that failed
        error: The exception that occurred
        user_message: Optional user-friendly message
    """
    logger.error(f"Error in {operation}: {error}", exc_info=True)
    if user_message:
        logger.info(f"User message: {user_message}")

# Custom exception classes for better error handling
class DatabaseError(Exception):
    """Database related errors"""
    pass

class SecurityError(Exception):
    """Security related errors"""
    pass

class ValidationError(Exception):
    """Validation related errors"""
    pass

class FileOperationError(Exception):
    """File operation related errors"""
    pass
