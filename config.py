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
        
        # Year validation settings
        self.MIN_YEAR = self._validate_non_negative_int(os.getenv('TAHQIQ_MIN_YEAR', '0'), 'MIN_YEAR', 0)
        self.MAX_YEAR = self._validate_positive_int(os.getenv('TAHQIQ_MAX_YEAR', '3000'), 'MAX_YEAR', 10000)
        
        # Database query limits
        self.DEFAULT_QUERY_LIMIT = self._validate_positive_int(os.getenv('TAHQIQ_DEFAULT_QUERY_LIMIT', '100'), 'DEFAULT_QUERY_LIMIT', 1000)
        self.MAX_QUERY_LIMIT = self._validate_positive_int(os.getenv('TAHQIQ_MAX_QUERY_LIMIT', '1000'), 'MAX_QUERY_LIMIT', 10000)
        
        # Database connection pooling
        self.DB_POOL_SIZE = self._validate_positive_int(os.getenv('TAHQIQ_DB_POOL_SIZE', '20'), 'DB_POOL_SIZE', 50)
        self.DB_POOL_MAX_OVERFLOW = self._validate_positive_int(os.getenv('TAHQIQ_DB_POOL_MAX_OVERFLOW', '30'), 'DB_POOL_MAX_OVERFLOW', 100)
        self.DB_POOL_TIMEOUT = self._validate_positive_int(os.getenv('TAHQIQ_DB_POOL_TIMEOUT', '30'), 'DB_POOL_TIMEOUT', 100)
        self.DB_POOL_RECYCLE = self._validate_positive_int(os.getenv('TAHQIQ_DB_POOL_RECYCLE', '3600'), 'DB_POOL_RECYCLE', 10000)
        
        # Paths
        self.BASE_DIR = Path(__file__).parent
        self.RESOURCES_DIR = self.BASE_DIR / 'views' / 'resources'
        self.STYLES_FILE = self.RESOURCES_DIR / 'styles.qss'
        
        # Validate configuration
        self._validate_all()
    
    def _validate_db_url(self, url):
        """Validate database URL with enhanced security"""
        if not url or not isinstance(url, str):
            raise ValueError("Database URL must be a non-empty string")
        
        # Whitelist allowed database protocols
        allowed_protocols = ['sqlite', 'postgresql', 'mysql', 'mariadb']
        protocol_match = re.match(r'^(\w+)://', url.lower())
        if not protocol_match:
            raise ValueError("Database URL must start with protocol (e.g., sqlite:///, postgresql://)")
        
        protocol = protocol_match.group(1)
        if protocol not in allowed_protocols:
            raise ValueError(f"Database protocol '{protocol}' not allowed. Allowed: {', '.join(allowed_protocols)}")
        
        # Enhanced security checks
        url_upper = url.upper()
        
        # SQL injection patterns
        sql_patterns = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'CREATE', 'ALTER', 'EXEC', 'UNION', 'SELECT',
            'WHERE', 'FROM', 'JOIN', 'INNER', 'OUTER', 'LEFT', 'RIGHT', 'GROUP', 'ORDER', 'HAVING'
        ]
        
        # Dangerous characters and patterns
        dangerous_patterns = [
            '..', ';', '--', '/*', '*/', '/*', '*/', 'xp_', 'sp_', '0x', 'char(', 'ascii(',
            'concat(', 'substring(', 'length(', 'version(', 'user(', 'database(',
            'waitfor', 'benchmark(', 'sleep(', 'pg_sleep(', 'information_schema'
        ]
        
        all_patterns = sql_patterns + dangerous_patterns
        for pattern in all_patterns:
            if pattern in url_upper:
                raise ValueError(f"Database URL contains dangerous pattern: {pattern}")
        
        # Additional validation for SQLite
        if protocol == 'sqlite':
            # SQLite path validation
            path_match = re.match(r'sqlite:///(.+)', url)
            if path_match:
                db_path = path_match.group(1)
                # Prevent path traversal
                if '..' in db_path or db_path.startswith('/') or ':' in db_path:
                    raise ValueError("SQLite database path must be relative and within application directory")
                # Ensure it has .db extension
                if not db_path.endswith('.db'):
                    raise ValueError("SQLite database file must have .db extension")
        
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
    
    def _validate_non_negative_int(self, value, name, max_value=None):
        """Validate non-negative integer configuration value"""
        try:
            int_value = int(value)
            if int_value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
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
    class FallbackConfig:
        def __init__(self):
            self.DATABASE_URL = 'sqlite:///tahqiq_data.db'
            self.LOG_LEVEL = 'INFO'
            self.LOG_FILE = 'tahqiq.log'
            self.APP_NAME = 'Tahqiq App'
            self.APP_VERSION = '1.0.0'
            self.MAX_TEXT_LENGTH = 10000
            self.MAX_NAME_LENGTH = 200
            self.MAX_TITLE_LENGTH = 300
            self.DEFAULT_PAGE_SIZE = 50
            self.MAX_PAGE_SIZE = 1000
            self.MIN_YEAR = 0
            self.MAX_YEAR = 3000
            self.DEFAULT_QUERY_LIMIT = 100
            self.MAX_QUERY_LIMIT = 1000
            self.BASE_DIR = Path(__file__).parent
            self.RESOURCES_DIR = Path(__file__).parent / 'views' / 'resources'
            self.STYLES_FILE = Path(__file__).parent / 'views' / 'resources' / 'styles.qss'
        
        def setup_logging(self):
            """Setup basic logging for fallback config"""
            log_level = getattr(logging, self.LOG_LEVEL.upper(), logging.INFO)
            logging.basicConfig(
                level=log_level,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(self.LOG_FILE, encoding='utf-8'),
                    logging.StreamHandler()
                ]
            )
            return logging.getLogger(__name__)
    
    config = FallbackConfig()
