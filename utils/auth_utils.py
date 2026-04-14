import hashlib
import secrets
import logging
from typing import Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AuthUtils:
    """Utility class for authentication operations"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA-256 with salt"""
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters long")
        
        # Generate a random salt
        salt = secrets.token_hex(16)
        
        # Combine password and salt
        password_salt = f"{password}{salt}"
        
        # Hash the combined string
        password_hash = hashlib.sha256(password_salt.encode()).hexdigest()
        
        # Store salt and hash together
        return f"{salt}${password_hash}"
    
    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """Verify a password against stored hash"""
        if not password or not stored_hash or '$' not in stored_hash:
            return False
        
        try:
            # Split only on the first $ to handle passwords containing $
            parts = stored_hash.split('$', 1)
            if len(parts) != 2:
                return False
            
            salt, hash_value = parts
            
            # Hash the provided password with the same salt
            password_salt = f"{password}{salt}"
            computed_hash = hashlib.sha256(password_salt.encode()).hexdigest()
            
            return computed_hash == hash_value
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        if not email:
            return False
        
        email = email.strip()
        
        # Basic email validation
        if len(email) > 255 or '@' not in email or '.' not in email:
            return False
        
        # Check for basic structure
        parts = email.split('@')
        if len(parts) != 2:
            return False
        
        local, domain = parts
        if not local or not domain:
            return False
        
        # Check domain has at least one dot
        if '.' not in domain:
            return False
        
        return True
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """Validate username format"""
        if not username:
            return False, "Username is required"
        
        username = username.strip()
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        if len(username) > 50:
            return False, "Username cannot exceed 50 characters"
        
        # Check for allowed characters (letters, numbers, underscore)
        if not username.replace('_', '').isalnum():
            return False, "Username can only contain letters, numbers, and underscores"
        
        return True, "Username is valid"
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """Validate password strength"""
        if not password:
            return False, "Password is required"
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"
        
        if len(password) > 128:
            return False, "Password cannot exceed 128 characters"
        
        # Check for at least one letter and one number
        has_letter = any(c.isalpha() for c in password)
        has_number = any(c.isdigit() for c in password)
        
        if not has_letter or not has_number:
            return False, "Password must contain at least one letter and one number"
        
        return True, "Password is valid"

class SessionManager:
    """Manages user sessions"""
    
    def __init__(self):
        self.current_user = None
        self.session_start = None
        self.session_timeout = timedelta(hours=24)  # 24-hour session
    
    def login(self, user):
        """Start a new session for the user"""
        self.current_user = user
        self.session_start = datetime.utcnow()
        logger.info(f"User {user.username} logged in")
    
    def logout(self):
        """End the current session"""
        if self.current_user:
            logger.info(f"User {self.current_user.username} logged out")
        self.current_user = None
        self.session_start = None
    
    def is_logged_in(self) -> bool:
        """Check if user is currently logged in"""
        if not self.current_user or not self.session_start:
            return False
        
        # Check if session has expired
        if datetime.utcnow() - self.session_start > self.session_timeout:
            self.logout()
            return False
        
        return True
    
    def get_current_user(self):
        """Get the currently logged in user"""
        if self.is_logged_in():
            return self.current_user
        return None
    
    def is_session_expired(self) -> bool:
        """Check if current session has expired"""
        if not self.session_start:
            return True
        
        return datetime.utcnow() - self.session_start > self.session_timeout

# Global session manager instance
session_manager = SessionManager()
