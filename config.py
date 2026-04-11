import os
import logging
from pathlib import Path
import re

class Config:
    """Application configuration with environment variable support"""
    
    def __init__(self):
        # Database configuration
        self.DATABASE_URL = self._validate_db_url(os.getenv('TAHQIQ_DB_URL', 'sqlite:///tahqiq_data.db'))
        
        # Logging configuration
        self.LOG_LEVEL = self._validate_log_level(os.getenv('TAHQIQ_LOG_LEVEL', 'INFO'))
        self.LOG_FILE = self._validate_log_file(os.getenv('TAHQIQ_LOG_FILE', 'tahqiq.log'))
        
        # Application settings
        self.APP_NAME = "Tahqiq App"
        self.APP_VERSION = "1.0.0"
        
        # Security settings
        self.MAX_TEXT_LENGTH = self._validate_positive_int(os.getenv('TAHQIQ_MAX_TEXT_LENGTH', '10000'), 'MAX_TEXT_LENGTH', 100000)
        self.MAX_NAME_LENGTH = self._validate_positive_int(os.getenv('TAHQIQ_MAX_NAME_LENGTH', '200'), 'MAX_NAME_LENGTH', 1000)
        self.MAX_TITLE_LENGTH = self._validate_positive_int(os.getenv('TAHQIQ_MAX_TITLE_LENGTH', '300'), 'MAX_TITLE_LENGTH', 2000)
        
        # Pagination settings
        self.DEFAULT_PAGE_SIZE = self._validate_positive_int(os.getenv('TAHQIQ_DEFAULT_PAGE_SIZE', '50'), 'DEFAULT_PAGE_SIZE', 500)
        self.MAX_PAGE_SIZE = self._validate_positive_int(os.getenv('TAHQIQ_MAX_PAGE_SIZE', '1000'), 'MAX_PAGE_SIZE', 10000)
        
        # Paths
        self.BASE_DIR = Path(__file__).parent
        self.RESOURCES_DIR = self.BASE_DIR / 'views' / 'resources'
        self.STYLES_FILE = self.RESOURCES_DIR / 'styles.qss'
        
        # Validate configuration
        self._validate_all()
    
    def _validate_db_url(self, url):
        """Validate database URL"""
        if not url or not isinstance(url, str):
            raise ValueError("Database URL must be a non-empty string")
        
        # Basic URL pattern validation
        if not re.match(r'^\w+://', url):
            raise ValueError("Database URL must start with protocol (e.g., sqlite:///, postgresql://)")
        
        # Check for dangerous patterns
        dangerous_patterns = ['..', ';', '--', '/*', '*/', 'DROP', 'DELETE', 'INSERT', 'UPDATE']
        url_upper = url.upper()
        for pattern in dangerous_patterns:
            if pattern in url_upper:
                raise ValueError(f"Database URL contains dangerous pattern: {pattern}")
        
        return url
    
    def _validate_log_level(self, level):
        """Validate log level"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if level.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {', '.join(valid_levels)}")
        return level.upper()
    
    def _validate_log_file(self, filename):
        """Validate log file name"""
        if not filename or not isinstance(filename, str):
            raise ValueError("Log file must be a non-empty string")
        
        # Check for dangerous characters
        if re.search(r'[<>:"|?*\x00-\x1f]', filename):
            raise ValueError("Log file contains invalid characters")
        
        # Check for path traversal
        if '..' in filename or filename.startswith('/'):
            raise ValueError("Log file path is invalid")
        
        return filename
    
    def _validate_positive_int(self, value, name, max_value=None):
        """Validate positive integer configuration value"""
        try:
            int_value = int(value)
            if int_value <= 0:
                raise ValueError(f"{name} must be a positive integer")
            if max_value and int_value > max_value:
                raise ValueError(f"{name} cannot exceed {max_value}")
            return int_value
        except (ValueError, TypeError):
            raise ValueError(f"{name} must be a valid integer")
    
    def _validate_all(self):
        """Validate all configuration values"""
        # Validate logical relationships
        if self.DEFAULT_PAGE_SIZE > self.MAX_PAGE_SIZE:
            raise ValueError("DEFAULT_PAGE_SIZE cannot exceed MAX_PAGE_SIZE")
        
        if self.MAX_NAME_LENGTH > self.MAX_TEXT_LENGTH:
            raise ValueError("MAX_NAME_LENGTH cannot exceed MAX_TEXT_LENGTH")
        
        if self.MAX_TITLE_LENGTH > self.MAX_TEXT_LENGTH:
            raise ValueError("MAX_TITLE_LENGTH cannot exceed MAX_TEXT_LENGTH")
        
        # Validate paths exist
        if not self.BASE_DIR.exists():
            raise ValueError("Base directory does not exist")
        
        if not self.RESOURCES_DIR.exists():
            self.RESOURCES_DIR.mkdir(parents=True, exist_ok=True)
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.LOG_LEVEL.upper(), logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_file_path = self.BASE_DIR / self.LOG_FILE
        log_file_path.parent.mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file_path, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
        # Set specific logger levels
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
        
        return logging.getLogger(__name__)

# Global configuration instance
try:
    config = Config()
except Exception as e:
    print(f"Configuration Error: {e}")
    print("Using default configuration...")
    # Fallback to safe defaults
    config = type('Config', (), {
        'DATABASE_URL': 'sqlite:///tahqiq_data.db',
        'LOG_LEVEL': 'INFO',
        'LOG_FILE': 'tahqiq.log',
        'APP_NAME': 'Tahqiq App',
        'APP_VERSION': '1.0.0',
        'MAX_TEXT_LENGTH': 10000,
        'MAX_NAME_LENGTH': 200,
        'MAX_TITLE_LENGTH': 300,
        'DEFAULT_PAGE_SIZE': 50,
        'MAX_PAGE_SIZE': 1000,
        'BASE_DIR': Path(__file__).parent,
        'RESOURCES_DIR': Path(__file__).parent / 'views' / 'resources',
        'STYLES_FILE': Path(__file__).parent / 'views' / 'resources' / 'styles.qss',
        'setup_logging': lambda: logging.getLogger(__name__)
    })()
