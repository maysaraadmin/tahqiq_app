"""
Standardized exception handling utilities for the application
"""
import logging
from typing import Optional, Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)

class ApplicationError(Exception):
    """Base exception for application-specific errors"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}

class ValidationError(ApplicationError):
    """Raised when input validation fails"""
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field
        self.value = value

class DatabaseError(ApplicationError):
    """Raised when database operations fail"""
    def __init__(self, message: str, operation: str = None, table: str = None):
        super().__init__(message, "DATABASE_ERROR")
        self.operation = operation
        self.table = table

class SecurityError(ApplicationError):
    """Raised when security validation fails"""
    def __init__(self, message: str, threat_type: str = None):
        super().__init__(message, "SECURITY_ERROR")
        self.threat_type = threat_type

def handle_exceptions(
    default_message: str = "An unexpected error occurred",
    error_type: type = ApplicationError,
    log_level: int = logging.ERROR,
    reraise: bool = True
):
    """
    Decorator for standardized exception handling
    
    Args:
        default_message: Default message for unexpected errors
        error_type: Type of exception to convert to
        log_level: Logging level for the error
        reraise: Whether to reraise the exception after logging
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ApplicationError as e:
                # Log application-specific errors
                logger.log(log_level, f"{func.__name__} failed: {e}", extra={
                    'error_code': e.error_code,
                    'details': e.details
                })
                if reraise:
                    raise
                return None
            except ValueError as e:
                # Convert ValueError to ValidationError
                validation_error = ValidationError(str(e))
                logger.log(log_level, f"{func.__name__} validation failed: {e}")
                if reraise:
                    raise validation_error
                return None
            except Exception as e:
                # Handle unexpected errors
                logger.log(log_level, f"{func.__name__} failed unexpectedly: {e}", exc_info=True)
                if reraise:
                    raise error_type(default_message, details={'original_error': str(e)})
                return None
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
    
    Returns:
        Function result or default_return on error
    """
    try:
        return func()
    except ApplicationError as e:
        if log_error:
            logger.error(f"{error_message}: {e}")
        return default_return
    except Exception as e:
        if log_error:
            logger.error(f"{error_message}: {e}", exc_info=True)
        return default_return

def log_exception(
    message: str,
    exception: Exception,
    level: int = logging.ERROR,
    extra_data: dict = None
):
    """
    Log an exception with standardized format
    
    Args:
        message: Log message
        exception: Exception to log
        level: Log level
        extra_data: Additional data to include in log
    """
    extra = extra_data or {}
    if isinstance(exception, ApplicationError):
        extra.update({
            'error_code': exception.error_code,
            'details': exception.details
        })
    
    logger.log(level, message, exc_info=True, extra=extra)

class ErrorContext:
    """Context manager for error handling"""
    
    def __init__(self, operation: str, default_message: str = None):
        self.operation = operation
        self.default_message = default_message or f"Error during {operation}"
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            if issubclass(exc_type, ApplicationError):
                logger.error(f"{self.operation} failed: {exc_val}", extra={
                    'error_code': exc_val.error_code,
                    'details': exc_val.details
                })
            else:
                logger.error(f"{self.operation} failed unexpectedly: {exc_val}", exc_info=True)
        return False  # Don't suppress exceptions
