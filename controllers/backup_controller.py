"""
Backup and export controller for data management
"""
import json
import csv
import sqlite3
from datetime import datetime
from pathlib import Path
from database.db_manager import DatabaseManager
from database.models import Author, Book, Manuscript, SheikhRelation
from controllers.base_controller import BaseController
from config import config
import logging

logger = logging.getLogger(__name__)

class BackupController(BaseController):
    """Controller for data backup and export operations"""
    
    def __init__(self):
        super().__init__()
    
    def export_to_json(self, file_path=None):
        """Export all data to JSON format"""
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = config.BASE_DIR / f"tahqiq_backup_{timestamp}.json"
        
        def export_transaction(session):
            # Get all data
            authors = session.query(Author).all()
            books = session.query(Book).all()
            manuscripts = session.query(Manuscript).all()
            relations = session.query(SheikhRelation).all()
            
            # Convert to serializable format
            data = {
                "export_date": datetime.now().isoformat(),
                "version": config.APP_VERSION,
                "authors": [
                    {
                        "id": a.id,
                        "name": a.name,
                        "birth_year": a.birth_year,
                        "death_year": a.death_year,
                        "bio": a.bio
                    } for a in authors
                ],
                "books": [
                    {
                        "id": b.id,
                        "title": b.title,
                        "author_id": b.author_id,
                        "description": b.description
                    } for b in books
                ],
                "manuscripts": [
                    {
                        "id": m.id,
                        "book_id": m.book_id,
                        "library_name": m.library_name,
                        "shelf_number": m.shelf_number,
                        "copyist": m.copyist,
                        "copy_date": m.copy_date,
                        "notes": m.notes
                    } for m in manuscripts
                ],
                "relations": [
                    {
                        "id": r.id,
                        "student_id": r.student_id,
                        "sheikh_id": r.sheikh_id,
                        "relation_type": r.relation_type
                    } for r in relations
                ]
            }
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Data exported to JSON: {file_path}")
            return str(file_path)
        
        try:
            return self.execute_in_transaction(export_transaction)
        except Exception as e:
            logger.error(f"JSON export failed: {e}")
            raise
    
    def export_to_csv(self, export_dir=None):
        """Export data to CSV files"""
        if export_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_dir = config.BASE_DIR / f"tahqiq_export_{timestamp}"
        
        export_dir = Path(export_dir)
        export_dir.mkdir(exist_ok=True)
        
        def export_authors_csv(session):
            authors = session.query(Author).all()
            with open(export_dir / "authors.csv", 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Name', 'Birth Year', 'Death Year', 'Bio'])
                for a in authors:
                    writer.writerow([a.id, a.name, a.birth_year, a.death_year, a.bio])
        
        def export_books_csv(session):
            books = session.query(Book).all()
            with open(export_dir / "books.csv", 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Title', 'Author ID', 'Description'])
                for b in books:
                    writer.writerow([b.id, b.title, b.author_id, b.description])
        
        def export_relations_csv(session):
            relations = session.query(SheikhRelation).all()
            with open(export_dir / "relations.csv", 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Student ID', 'Sheikh ID', 'Relation Type'])
                for r in relations:
                    writer.writerow([r.id, r.student_id, r.sheikh_id, r.relation_type])
        
        try:
            self.execute_in_transaction(export_authors_csv)
            self.execute_in_transaction(export_books_csv)
            self.execute_in_transaction(export_relations_csv)
            
            logger.info(f"Data exported to CSV: {export_dir}")
            return str(export_dir)
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            raise
    
    def create_database_backup(self, backup_path=None):
        """Create a complete database backup"""
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = config.BASE_DIR / f"tahqiq_db_backup_{timestamp}.db"
        
        try:
            # Get the current database path
            if config.DATABASE_URL.startswith('sqlite:///'):
                current_db = config.BASE_DIR / config.DATABASE_URL[10:]  # Remove 'sqlite:///'
                
                if current_db.exists():
                    # Copy the database file
                    import shutil
                    shutil.copy2(current_db, backup_path)
                    logger.info(f"Database backup created: {backup_path}")
                    return str(backup_path)
                else:
                    raise ValueError("Database file not found")
            else:
                raise ValueError("Database backup only supported for SQLite")
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            raise
    
    def get_export_summary(self):
        """Get summary of data for export"""
        def summary_transaction(session):
            author_count = session.query(Author).count()
            book_count = session.query(Book).count()
            manuscript_count = session.query(Manuscript).count()
            relation_count = session.query(SheikhRelation).count()
            
            return {
                "authors": author_count,
                "books": book_count,
                "manuscripts": manuscript_count,
                "relations": relation_count,
                "total": author_count + book_count + manuscript_count + relation_count
            }
        
        try:
            return self.execute_in_transaction(summary_transaction)
        except Exception as e:
            logger.error(f"Failed to get export summary: {e}")
            raise
