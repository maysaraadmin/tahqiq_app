"""
Base controller with common functionality for all controllers
"""
from database.db_manager import DatabaseManager
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession
from contextlib import contextmanager
import logging
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)

class BaseController:
    """Base controller with common database operations"""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def get_transaction_session(self, isolation_level=None):
        """Get a session with specific isolation level for transactions"""
        if isolation_level:
            # Create a session with specific isolation level
            Session = sessionmaker(bind=self.db.engine, isolation_level=isolation_level)
            return Session()
        else:
            # Use default session
            return self.db.get_session()
    
    @contextmanager
    def get_session_context(self, isolation_level=None):
        """Context manager for automatic session cleanup"""
        session = self.get_transaction_session(isolation_level)
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Session context error: {e}")
            raise
        finally:
            self._safe_close_session(session)
    
    def execute_in_transaction(self, func: Callable[[SQLAlchemySession], Any], isolation_level: Optional[str] = None):
        """Execute a function within a database transaction with enhanced error handling"""
        session = self.get_transaction_session(isolation_level)
        try:
            result = func(session)
            session.commit()
            return result
        except Exception as e:
            try:
                session.rollback()
            except Exception as rollback_error:
                logger.error(f"Failed to rollback transaction: {rollback_error}")
            logger.error(f"Transaction failed: {e}")
            raise
        finally:
            self._safe_close_session(session)
    
    def _safe_close_session(self, session):
        """Safely close session with error handling"""
        try:
            if session and hasattr(session, 'close'):
                self.db.close_session(session)
        except Exception as e:
            logger.error(f"Error closing session: {e}")
    
    def execute_with_retry(self, func: Callable[[SQLAlchemySession], Any], max_retries: int = 3, isolation_level: Optional[str] = None):
        """Execute function with retry logic for transient errors"""
        for attempt in range(max_retries):
            try:
                return self.execute_in_transaction(func, isolation_level)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Attempt {attempt + 1} failed, retrying: {e}")
                import time
                time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
    
    def validate_id(self, id_value, entity_name="ID"):
        """Common ID validation"""
        try:
            id_int = int(id_value)
            if id_int <= 0:
                raise ValueError(f"{entity_name} must be a positive integer")
            return id_int
        except (ValueError, TypeError):
            raise ValueError(f"{entity_name} must be a valid number")
