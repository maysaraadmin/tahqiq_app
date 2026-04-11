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
    _engine = None
    _session_factory = None

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    logger.info("Creating new DatabaseManager instance")
        return cls._instance

    def __init__(self, db_url=None):
        with self._lock:
            if self._engine is None:
                try:
                    # Use configuration if no URL provided
                    if db_url is None:
                        db_url = config.DATABASE_URL
                    
                    self._engine = create_engine(
                        db_url, 
                        echo=False, 
                        pool_pre_ping=True,
                        pool_size=10,
                        max_overflow=20,
                        pool_timeout=30
                    )
                    self._session_factory = sessionmaker(bind=self._engine)
                    Base.metadata.create_all(self._engine)
                    logger.info(f"Database initialized successfully with URL: {db_url}")
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

    def close_all(self):
        if self._engine:
            self._engine.dispose()
            logger.info("Database connections closed")
