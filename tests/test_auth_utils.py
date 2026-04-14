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
    
    def test_session_creation(self):
        """Test session creation"""
        user_id = 1
        session_id = self.session_manager.create_session(user_id)
        
        self.assertIsNotNone(session_id)
        self.assertTrue(len(session_id) > 10)
        self.assertEqual(self.session_manager.get_user_id(session_id), user_id)
    
    def test_session_validation(self):
        """Test session validation"""
        user_id = 1
        session_id = self.session_manager.create_session(user_id)
        
        # Valid session should validate
        self.assertTrue(self.session_manager.validate_session(session_id))
        
        # Invalid session should not validate
        self.assertFalse(self.session_manager.validate_session("invalid_session"))
    
    def test_session_destruction(self):
        """Test session destruction"""
        user_id = 1
        session_id = self.session_manager.create_session(user_id)
        
        # Session should exist before destruction
        self.assertTrue(self.session_manager.validate_session(session_id))
        
        # Destroy session
        self.session_manager.destroy_session(session_id)
        
        # Session should not exist after destruction
        self.assertFalse(self.session_manager.validate_session(session_id))
        self.assertIsNone(self.session_manager.get_user_id(session_id))


if __name__ == '__main__':
    unittest.main()
