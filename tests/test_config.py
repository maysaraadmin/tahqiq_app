"""
Unit tests for configuration
"""

import unittest
import os
from config import Config


class TestConfig(unittest.TestCase):
    """Test configuration management"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Store original environment variables
        self.original_env = {}
        test_vars = [
            'TAHQIQ_DB_URL', 'TAHQIQ_LOG_LEVEL', 'TAHQIQ_LOG_FILE',
            'TAHQIQ_MAX_TEXT_LENGTH', 'TAHQIQ_MAX_NAME_LENGTH',
            'TAHQIQ_MAX_TITLE_LENGTH', 'TAHQIQ_DEFAULT_PAGE_SIZE',
            'TAHQIQ_MAX_PAGE_SIZE', 'TAHQIQ_MIN_YEAR', 'TAHQIQ_MAX_YEAR',
            'TAHQIQ_MAX_FILE_SIZE_MB', 'TAHQIQ_THREAD_TIMEOUT_MS'
        ]
        
        for var in test_vars:
            self.original_env[var] = os.getenv(var)
            if var in os.environ:
                del os.environ[var]
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Restore original environment variables
        for var, value in self.original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]
    
    def test_default_config(self):
        """Test default configuration values"""
        config = Config()
        
        # Test default values
        self.assertEqual(config.APP_NAME, "Tahqiq App")
        self.assertEqual(config.APP_VERSION, "1.0.0")
        self.assertEqual(config.LOG_LEVEL, "INFO")
        self.assertEqual(config.DEFAULT_PAGE_SIZE, 50)
        self.assertEqual(config.MAX_PAGE_SIZE, 1000)
        self.assertEqual(config.MIN_YEAR, 0)
        self.assertEqual(config.MAX_YEAR, 3000)
        self.assertEqual(config.MAX_FILE_SIZE_MB, 50)
        self.assertEqual(config.THREAD_TIMEOUT_MS, 5000)
    
    def test_environment_variables(self):
        """Test environment variable overrides"""
        # Set test environment variables
        os.environ['TAHQIQ_LOG_LEVEL'] = 'DEBUG'
        os.environ['TAHQIQ_MAX_FILE_SIZE_MB'] = '100'
        os.environ['TAHQIQ_THREAD_TIMEOUT_MS'] = '10000'
        
        config = Config()
        
        # Test overridden values
        self.assertEqual(config.LOG_LEVEL, 'DEBUG')
        self.assertEqual(config.MAX_FILE_SIZE_MB, 100)
        self.assertEqual(config.THREAD_TIMEOUT_MS, 10000)
    
    def test_file_size_calculation(self):
        """Test file size calculation"""
        config = Config()
        
        # Test default file size
        self.assertEqual(config.MAX_FILE_SIZE_MB, 50)
        self.assertEqual(config.MAX_FILE_SIZE_BYTES, 50 * 1024 * 1024)
        
        # Test custom file size
        os.environ['TAHQIQ_MAX_FILE_SIZE_MB'] = '100'
        config = Config()
        self.assertEqual(config.MAX_FILE_SIZE_MB, 100)
        self.assertEqual(config.MAX_FILE_SIZE_BYTES, 100 * 1024 * 1024)
    
    def test_validation_methods(self):
        """Test validation methods"""
        config = Config()
        
        # Test positive integer validation
        self.assertEqual(config._validate_positive_int('10', 'test'), 10)
        self.assertEqual(config._validate_positive_int('1', 'test'), 1)
        
        # Test non-negative integer validation
        self.assertEqual(config._validate_non_negative_int('0', 'test'), 0)
        self.assertEqual(config._validate_non_negative_int('10', 'test'), 10)
        
        # Test validation with defaults
        self.assertEqual(config._validate_positive_int('', 'test', 5), 5)
        self.assertEqual(config._validate_non_negative_int('', 'test', 0), 0)
    
    def test_invalid_values(self):
        """Test invalid value handling"""
        config = Config()
        
        # Test invalid positive integers
        with self.assertRaises(ValueError):
            config._validate_positive_int('0', 'test')
        
        with self.assertRaises(ValueError):
            config._validate_positive_int('-1', 'test')
        
        # Test invalid non-negative integers
        with self.assertRaises(ValueError):
            config._validate_non_negative_int('-1', 'test')
        
        # Test invalid strings
        with self.assertRaises(ValueError):
            config._validate_positive_int('abc', 'test')
    
    def test_log_level_validation(self):
        """Test log level validation"""
        config = Config()
        
        # Valid log levels
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        for level in valid_levels:
            result = config._validate_log_level(level)
            self.assertEqual(result, level)
        
        # Invalid log level
        with self.assertRaises(ValueError):
            config._validate_log_level('INVALID')
    
    def test_database_url_validation(self):
        """Test database URL validation"""
        config = Config()
        
        # Test that default URL is set correctly
        self.assertEqual(config.DATABASE_URL, 'sqlite:///tahqiq_data.db')
        
        # Test valid SQLite URLs
        valid_urls = [
            'sqlite:///test.db',
            'sqlite:///path/to/test.db'
        ]
        
        for url in valid_urls:
            result = config._validate_db_url(url)
            self.assertEqual(result, url)
        
        # Test invalid URLs
        with self.assertRaises(ValueError):
            config._validate_db_url('invalid-url')
        
        with self.assertRaises(ValueError):
            config._validate_db_url('http://example.com')
    
    def test_logical_relationships(self):
        """Test logical configuration relationships"""
        config = Config()
        
        # Test default values satisfy constraints
        self.assertLessEqual(config.DEFAULT_PAGE_SIZE, config.MAX_PAGE_SIZE)
        self.assertLessEqual(config.MAX_NAME_LENGTH, config.MAX_TEXT_LENGTH)
        self.assertLessEqual(config.MAX_TITLE_LENGTH, config.MAX_TEXT_LENGTH)
        
        # Test invalid relationships
        os.environ['TAHQIQ_DEFAULT_PAGE_SIZE'] = '1000'
        os.environ['TAHQIQ_MAX_PAGE_SIZE'] = '500'
        
        with self.assertRaises(ValueError):
            Config()  # Should raise validation error


if __name__ == '__main__':
    unittest.main()
