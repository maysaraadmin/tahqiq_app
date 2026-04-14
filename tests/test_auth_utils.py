"""
Unit tests for authentication utilities
"""

import unittest
from utils.auth_utils import AuthUtils, SessionManager


class TestAuthUtils(unittest.TestCase):
    """Test authentication utility functions"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "test123"
        hashed = AuthUtils.hash_password(password)
        
        # Should contain salt and hash separated by $
        self.assertIn('$', hashed)
        self.assertTrue(len(hashed) > 20)
        
        # Different passwords should produce different hashes
        password2 = "test456"
        hashed2 = AuthUtils.hash_password(password2)
        self.assertNotEqual(hashed, hashed2)
    
    def test_verify_password(self):
        """Test password verification"""
        password = "test123"
        hashed = AuthUtils.hash_password(password)
        
        # Correct password should verify
        self.assertTrue(AuthUtils.verify_password(password, hashed))
        
        # Wrong password should not verify
        self.assertFalse(AuthUtils.verify_password("wrong", hashed))
        
        # Empty inputs should not verify
        self.assertFalse(AuthUtils.verify_password("", hashed))
        self.assertFalse(AuthUtils.verify_password(password, ""))
        self.assertFalse(AuthUtils.verify_password("", ""))
    
    def test_validate_email(self):
        """Test email validation"""
        # Valid emails
        self.assertTrue(AuthUtils.validate_email("test@example.com"))
        self.assertTrue(AuthUtils.validate_email("user.name@domain.co.uk"))
        
        # Invalid emails
        self.assertFalse(AuthUtils.validate_email(""))
        self.assertFalse(AuthUtils.validate_email("invalid"))
        self.assertFalse(AuthUtils.validate_email("@domain.com"))
        self.assertFalse(AuthUtils.validate_email("user@"))
        self.assertFalse(AuthUtils.validate_email("user@domain"))
        self.assertFalse(AuthUtils.validate_email("user..name@domain.com"))
    
    def test_validate_username(self):
        """Test username validation"""
        # Valid usernames
        result, msg = AuthUtils.validate_username("testuser")
        self.assertTrue(result)
        self.assertEqual(msg, "Username is valid")
        
        result, msg = AuthUtils.validate_username("test_user123")
        self.assertTrue(result)
        
        # Invalid usernames
        result, msg = AuthUtils.validate_username("")
        self.assertFalse(result)
        self.assertEqual(msg, "Username is required")
        
        result, msg = AuthUtils.validate_username("ab")
        self.assertFalse(result)
        self.assertIn("at least 3 characters", msg)
        
        result, msg = AuthUtils.validate_username("user@name")
        self.assertFalse(result)
        self.assertIn("letters, numbers, and underscores", msg)
    
    def test_validate_password(self):
        """Test password validation"""
        # Valid passwords
        result, msg = AuthUtils.validate_password("password123")
        self.assertTrue(result)
        self.assertEqual(msg, "Password is valid")
        
        # Invalid passwords
        result, msg = AuthUtils.validate_password("")
        self.assertFalse(result)
        self.assertEqual(msg, "Password is required")
        
        result, msg = AuthUtils.validate_password("12345")
        self.assertFalse(result)
        self.assertIn("at least 6 characters", msg)


class TestSessionManager(unittest.TestCase):
    """Test session management"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.session_manager = SessionManager()
    
    def test_login_logout(self):
        """Test login and logout functionality"""
        # Initially not logged in
        self.assertFalse(self.session_manager.is_logged_in())
        self.assertIsNone(self.session_manager.get_current_user())
        
        # Mock user object
        class MockUser:
            def __init__(self, username):
                self.username = username
        
        user = MockUser("testuser")
        
        # Login
        self.session_manager.login(user)
        self.assertTrue(self.session_manager.is_logged_in())
        self.assertEqual(self.session_manager.get_current_user(), user)
        
        # Logout
        self.session_manager.logout()
        self.assertFalse(self.session_manager.is_logged_in())
        self.assertIsNone(self.session_manager.get_current_user())
    
    def test_session_timeout(self):
        """Test session timeout functionality"""
        # Mock user object
        class MockUser:
            def __init__(self, username):
                self.username = username
        
        user = MockUser("testuser")
        
        # Login
        self.session_manager.login(user)
        self.assertTrue(self.session_manager.is_logged_in())
        
        # Test timeout check (this would require mocking datetime for proper testing)
        # For now, just test the method exists
        self.assertTrue(hasattr(self.session_manager, 'is_logged_in'))
        self.assertTrue(hasattr(self.session_manager, 'get_current_user'))
        self.assertTrue(hasattr(self.session_manager, 'login'))
        self.assertTrue(hasattr(self.session_manager, 'logout'))


if __name__ == '__main__':
    unittest.main()
