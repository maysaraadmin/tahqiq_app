from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base
from config import config
import logging
import threading

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()
    _initialized = False
    _engine = None
    _session_factory = None

    def __new__(cls):
        # Double-checked locking pattern for thread safety
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    logger.info("Creating new DatabaseManager instance")
        return cls._instance

    def __init__(self, db_url=None):
        # Only initialize once, even with multiple threads
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    try:
                        # Use configuration if no URL provided
                        if db_url is None:
                            db_url = config.DATABASE_URL
                        
                        # Create engine with optimized settings for faster startup
                        # Optimize for SQLite
                        sqlite_args = {"check_same_thread": False, "timeout": 20} if "sqlite" in db_url else {"check_same_thread": False}
                        
                        # Enhanced connection pooling
                        pool_size = 20  # Limit number of connections
                        max_overflow = 30  # Allow some overflow
                        pool_timeout = 30  # Connection timeout
                        pool_recycle = 3600  # Recycle connections every hour
                        pool_pre_ping = True  # Verify connections before use
                        
                        self._engine = create_engine(
                            db_url,
                            echo=False,  # Disable SQL logging for performance
                            pool_size=pool_size,
                            max_overflow=max_overflow,
                            pool_timeout=pool_timeout,
                            pool_recycle=pool_recycle,
                            pool_pre_ping=pool_pre_ping,
                            connect_args=sqlite_args
                        )
                        
                        # Create session factory
                        self._session_factory = sessionmaker(bind=self._engine)
                        
                        # Create tables asynchronously if needed (faster startup)
                        if not hasattr(self, '_tables_created'):
                            Base.metadata.create_all(self._engine)
                            self._tables_created = True
                            logger.info("Database initialized successfully")
                        
                        self._initialized = True
                    except Exception as e:
                        logger.error(f"Failed to initialize database: {e}")
                        raise

    @property
    def engine(self):
        return self._engine

    def get_session(self):
        return self._session_factory()

    def close_session(self, session):
        if session:
            session.close()

    def execute_in_transaction(self, operation):
        """Execute a database operation within a transaction"""
        session = self.get_session()
        try:
            result = operation(session)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            logger.error(f"Transaction failed: {e}")
            raise
        finally:
            self.close_session(session)

    def close_all(self):
        if self._engine:
            self._engine.dispose()
            logger.info("Database connections closed")
    
    def close_all_connections(self):
        """Close all database connections (alias for close_all)"""
        self.close_all()
