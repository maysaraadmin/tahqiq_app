from sqlalchemy.orm import Session
from database.models import User
from database.db_manager import DatabaseManager
from utils.auth_utils import AuthUtils, session_manager
from datetime import datetime
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class AuthController:
    """Controller for authentication operations"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def signup(self, username: str, email: str, password: str, full_name: str = None) -> Tuple[bool, str]:
        """Register a new user"""
        try:
            # Validate input
            valid_username, username_msg = AuthUtils.validate_username(username)
            if not valid_username:
                return False, username_msg
            
            if not AuthUtils.validate_email(email):
                return False, "Invalid email format"
            
            valid_password, password_msg = AuthUtils.validate_password(password)
            if not valid_password:
                return False, password_msg
            
            # Check if user already exists
            session = self.db_manager.get_session()
            try:
                # Check username
                existing_user = session.query(User).filter(User.username == username).first()
                if existing_user:
                    return False, "Username already exists"
                
                # Check email
                existing_email = session.query(User).filter(User.email == email).first()
                if existing_email:
                    return False, "Email already registered"
                
                # Create new user
                password_hash = AuthUtils.hash_password(password)
                new_user = User(
                    username=username,
                    email=email,
                    password_hash=password_hash,
                    full_name=full_name,
                    created_at=datetime.utcnow(),
                    is_active=True
                )
                
                session.add(new_user)
                session.commit()
                
                logger.info(f"New user registered: {username}")
                return True, "Registration successful"
                
            except Exception as e:
                session.rollback()
                logger.error(f"Registration error: {e}")
                return False, "Registration failed. Please try again."
            finally:
                self.db_manager.close_session(session)
                
        except Exception as e:
            logger.error(f"Signup controller error: {e}")
            return False, "An unexpected error occurred"
    
    def login(self, username: str, password: str) -> Tuple[bool, str]:
        """Authenticate user login"""
        try:
            if not username or not password:
                return False, "Username and password are required"
            
            session = self.db_manager.get_session()
            try:
                # Find user by username or email
                user = session.query(User).filter(
                    (User.username == username) | (User.email == username)
                ).first()
                
                if not user:
                    return False, "Invalid username or password"
                
                if not user.is_active:
                    return False, "Account is deactivated"
                
                # Verify password
                if not AuthUtils.verify_password(password, user.password_hash):
                    return False, "Invalid username or password"
                
                # Update last login
                user.last_login = datetime.utcnow()
                session.commit()
                
                # Start session
                session_manager.login(user)
                
                logger.info(f"User logged in: {user.username}")
                return True, "Login successful"
                
            except Exception as e:
                session.rollback()
                logger.error(f"Login error: {e}")
                return False, "Login failed. Please try again."
            finally:
                self.db_manager.close_session(session)
                
        except Exception as e:
            logger.error(f"Login controller error: {e}")
            return False, "An unexpected error occurred"
    
    def logout(self) -> Tuple[bool, str]:
        """Logout current user"""
        try:
            if not session_manager.is_logged_in():
                return False, "No user is currently logged in"
            
            current_user = session_manager.get_current_user()
            session_manager.logout()
            
            logger.info(f"User logged out: {current_user.username if current_user else 'unknown'}")
            return True, "Logout successful"
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False, "Logout failed"
    
    def get_current_user(self) -> Optional[User]:
        """Get currently logged in user"""
        try:
            return session_manager.get_current_user()
        except Exception as e:
            logger.error(f"Get current user error: {e}")
            return None
    
    def is_logged_in(self) -> bool:
        """Check if user is logged in"""
        try:
            return session_manager.is_logged_in()
        except Exception as e:
            logger.error(f"Check login status error: {e}")
            return False
    
    def update_profile(self, user_id: int, full_name: str = None, email: str = None) -> Tuple[bool, str]:
        """Update user profile"""
        try:
            if not self.is_logged_in():
                return False, "You must be logged in to update your profile"
            
            current_user = self.get_current_user()
            if current_user.id != user_id:
                return False, "Unauthorized to update this profile"
            
            session = self.db_manager.get_session()
            try:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    return False, "User not found"
                
                # Update email if provided
                if email and email != user.email:
                    if not AuthUtils.validate_email(email):
                        return False, "Invalid email format"
                    
                    # Check if email is already taken by another user
                    existing_email = session.query(User).filter(
                        User.email == email, User.id != user_id
                    ).first()
                    if existing_email:
                        return False, "Email already registered by another user"
                    
                    user.email = email
                
                # Update full name if provided
                if full_name is not None:
                    user.full_name = full_name
                
                session.commit()
                
                logger.info(f"Profile updated for user: {user.username}")
                return True, "Profile updated successfully"
                
            except Exception as e:
                session.rollback()
                logger.error(f"Profile update error: {e}")
                return False, "Failed to update profile"
            finally:
                self.db_manager.close_session(session)
                
        except Exception as e:
            logger.error(f"Update profile controller error: {e}")
            return False, "An unexpected error occurred"
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password"""
        try:
            if not self.is_logged_in():
                return False, "You must be logged in to change your password"
            
            current_user = self.get_current_user()
            if current_user.id != user_id:
                return False, "Unauthorized to change this password"
            
            # Validate new password
            valid_password, password_msg = AuthUtils.validate_password(new_password)
            if not valid_password:
                return False, password_msg
            
            session = self.db_manager.get_session()
            try:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    return False, "User not found"
                
                # Verify current password
                if not AuthUtils.verify_password(current_password, user.password_hash):
                    return False, "Current password is incorrect"
                
                # Update password
                user.password_hash = AuthUtils.hash_password(new_password)
                session.commit()
                
                logger.info(f"Password changed for user: {user.username}")
                return True, "Password changed successfully"
                
            except Exception as e:
                session.rollback()
                logger.error(f"Password change error: {e}")
                return False, "Failed to change password"
            finally:
                self.db_manager.close_session(session)
                
        except Exception as e:
            logger.error(f"Change password controller error: {e}")
            return False, "An unexpected error occurred"

# Global auth controller instance
auth_controller = AuthController()
