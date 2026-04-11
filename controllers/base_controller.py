"""
Base controller with common functionality for all controllers
"""
from database.db_manager import DatabaseManager
from sqlalchemy.orm import sessionmaker
import logging

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
    
    def execute_in_transaction(self, func):
        """Execute a function within a database transaction"""
        session = self.db.get_session()
        try:
            result = func(session)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            logger.error(f"Transaction failed: {e}")
            raise
        finally:
            self.db.close_session(session)
    
    def validate_id(self, id_value, entity_name="ID"):
        """Common ID validation"""
        try:
            id_int = int(id_value)
            if id_int <= 0:
                raise ValueError(f"{entity_name} must be a positive integer")
            return id_int
        except (ValueError, TypeError):
            raise ValueError(f"{entity_name} must be a valid number")
