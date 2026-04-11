import json
import logging
from pathlib import Path
from datetime import datetime
from sqlalchemy import text, create_engine, MetaData, Table, Column, Integer, String, DateTime
from database.db_manager import DatabaseManager
from database.models import Base
from config import config

logger = logging.getLogger(__name__)

class MigrationManager:
    """Simple migration management system"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.migrations_dir = Path(__file__).parent
        self.migration_table = "schema_migrations"
    
    def ensure_migration_table(self):
        """Create migration tracking table if it doesn't exist"""
        session = self.db_manager.get_session()
        try:
            # Validate table name to prevent SQL injection
            if not self._is_valid_table_name(self.migration_table):
                raise ValueError(f"Invalid table name: {self.migration_table}")
            
            # Use SQLAlchemy Core for safe table creation
            metadata = MetaData()
            migration_table = Table(
                self.migration_table,
                metadata,
                Column('id', Integer, primary_key=True),
                Column('version', String(50), nullable=False, unique=True),
                Column('applied_at', DateTime, server_default=text('CURRENT_TIMESTAMP'))
            )
            
            # Create table safely
            migration_table.create(self.db_manager.engine, checkfirst=True)
            logger.info(f"Migration table {self.migration_table} ensured")
        except Exception as e:
            logger.error(f"Failed to create migration table: {e}")
            raise
        finally:
            self.db_manager.close_session()
    
    def _is_valid_table_name(self, table_name):
        """Validate table name to prevent SQL injection"""
        import re
        # Only allow alphanumeric characters and underscores
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name))
    
    def get_applied_migrations(self):
        """Get list of applied migrations"""
        session = self.db_manager.get_session()
        try:
            # Use parameterized query
            query = text(f"SELECT version FROM {self.migration_table} ORDER BY version")
            result = session.execute(query)
            return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return []
        finally:
            self.db_manager.close_session()
    
    def get_pending_migrations(self):
        """Get list of pending migrations"""
        applied = set(self.get_applied_migrations())
        
        migration_files = []
        for file_path in self.migrations_dir.glob("*.json"):
            if file_path.name != "__init__.py" and file_path.suffix == ".json":
                version = file_path.stem
                if version not in applied:
                    migration_files.append((version, file_path))
        
        return sorted(migration_files, key=lambda x: x[0])
    
    def apply_migration(self, version, file_path):
        """Apply a single migration"""
        session = self.db_manager.get_session()
        try:
            # Read migration file
            with open(file_path, 'r', encoding='utf-8') as f:
                migration_data = json.load(f)
            
            # Execute migration SQL
            if 'up' in migration_data and migration_data['up']:
                for sql in migration_data['up']:
                    session.execute(sql)
            
            # Record migration safely
            query = text(f"INSERT INTO {self.migration_table} (version) VALUES (:version)")
            session.execute(query, {"version": version})
            
            session.commit()
            logger.info(f"Applied migration: {version}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to apply migration {version}: {e}")
            return False
        finally:
            self.db_manager.close_session()
    
    def rollback_migration(self, version, file_path):
        """Rollback a migration"""
        session = self.db_manager.get_session()
        try:
            # Read migration file
            with open(file_path, 'r', encoding='utf-8') as f:
                migration_data = json.load(f)
            
            # Execute rollback SQL
            if 'down' in migration_data and migration_data['down']:
                for sql in migration_data['down']:
                    session.execute(sql)
            
            # Remove migration record safely
            query = text(f"DELETE FROM {self.migration_table} WHERE version = :version")
            session.execute(query, {"version": version})
            
            session.commit()
            logger.info(f"Rolled back migration: {version}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to rollback migration {version}: {e}")
            return False
        finally:
            self.db_manager.close_session()
    
    def migrate_up(self):
        """Apply all pending migrations"""
        logger.info("Starting migration up")
        self.ensure_migration_table()
        
        pending = self.get_pending_migrations()
        if not pending:
            logger.info("No pending migrations")
            return True
        
        success_count = 0
        for version, file_path in pending:
            if self.apply_migration(version, file_path):
                success_count += 1
            else:
                logger.error(f"Migration failed at version: {version}")
                return False
        
        logger.info(f"Applied {success_count} migrations successfully")
        return True
    
    def migrate_down(self, target_version=None):
        """Rollback migrations"""
        logger.info("Starting migration down")
        applied = self.get_applied_migrations()
        
        if not applied:
            logger.info("No migrations to rollback")
            return True
        
        # Determine which migrations to rollback
        if target_version:
            to_rollback = [v for v in applied if v > target_version]
        else:
            # Rollback the last migration only
            to_rollback = [applied[-1]] if applied else []
        
        success_count = 0
        for version in reversed(to_rollback):
            file_path = self.migrations_dir / f"{version}.json"
            if file_path.exists():
                if self.rollback_migration(version, file_path):
                    success_count += 1
                else:
                    logger.error(f"Rollback failed at version: {version}")
                    return False
            else:
                logger.warning(f"Migration file not found: {version}")
        
        logger.info(f"Rolled back {success_count} migrations successfully")
        return True
    
    def create_migration(self, description):
        """Create a new migration file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version = f"{timestamp}_{description.replace(' ', '_')}"
        
        migration_file = self.migrations_dir / f"{version}.json"
        
        migration_template = {
            "version": version,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "up": [
                "-- Add your SQL statements here"
            ],
            "down": [
                "-- Add rollback SQL statements here"
            ]
        }
        
        with open(migration_file, 'w', encoding='utf-8') as f:
            json.dump(migration_template, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created migration file: {migration_file}")
        return migration_file

# Global migration manager instance
migration_manager = MigrationManager()
