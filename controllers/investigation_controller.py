import os
import shutil
from datetime import datetime
from typing import List, Dict, Optional
from database.db_manager import DatabaseManager
from database.models import BookInvestigation, InvestigationFile, ManuscriptComparison, ComparisonDetail, Book, Manuscript
import logging
import json

logger = logging.getLogger(__name__)

class InvestigationController:
    def __init__(self):
        self.db = DatabaseManager()
        self.upload_dir = "uploads/investigations"
        self._ensure_upload_directory()

    def _ensure_upload_directory(self):
        """Ensure upload directory exists"""
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir, exist_ok=True)

    def create_investigation(self, book_id: int, user_id: int, title: str = None, 
                           description: str = None, methodology: str = None, 
                           objectives: str = None) -> int:
        """Create a new book investigation"""
        def create_investigation_transaction(session):
            # Validate book exists
            book = session.query(Book).get(book_id)
            if not book:
                raise ValueError("Book not found")
            
            # Create investigation
            investigation = BookInvestigation(
                book_id=book_id,
                user_id=user_id,
                title=title or f"Investigation of {book.title}",
                description=description,
                methodology=methodology,
                objectives=objectives,
                status='in_progress',
                start_date=datetime.utcnow()
            )
            
            session.add(investigation)
            session.flush()
            logger.info(f"Created investigation: {investigation.title} (ID: {investigation.id})")
            return investigation.id
        
        try:
            return self.db.execute_in_transaction(create_investigation_transaction)
        except Exception as e:
            logger.error(f"Failed to create investigation: {e}")
            raise

    def get_user_investigations(self, user_id: int) -> List[Dict]:
        """Get all investigations for a user"""
        session = self.db.get_session()
        try:
            investigations = session.query(BookInvestigation).filter(
                BookInvestigation.user_id == user_id
            ).order_by(BookInvestigation.start_date.desc()).all()
            
            result = []
            for inv in investigations:
                result.append({
                    'id': inv.id,
                    'title': inv.title,
                    'book_title': inv.book.title,
                    'book_id': inv.book_id,
                    'status': inv.status,
                    'start_date': inv.start_date.isoformat() if inv.start_date else None,
                    'completion_date': inv.completion_date.isoformat() if inv.completion_date else None,
                    'description': inv.description,
                    'files_count': len(inv.uploaded_files),
                    'comparisons_count': len(inv.comparisons)
                })
            
            return result
        except Exception as e:
            logger.error(f"Failed to get user investigations: {e}")
            raise
        finally:
            self.db.close_session(session)

    def get_investigation_details(self, investigation_id: int) -> Dict:
        """Get detailed information about an investigation"""
        session = self.db.get_session()
        try:
            investigation = session.query(BookInvestigation).get(investigation_id)
            if not investigation:
                raise ValueError("Investigation not found")
            
            # Get files
            files = []
            for file in investigation.uploaded_files:
                files.append({
                    'id': file.id,
                    'filename': file.original_filename or file.filename,
                    'file_type': file.file_type,
                    'file_size': file.file_size,
                    'upload_date': file.upload_date.isoformat(),
                    'description': file.description,
                    'is_primary': file.is_primary,
                    'manuscript_id': file.manuscript_id
                })
            
            # Get comparisons
            comparisons = []
            for comp in investigation.comparisons:
                comparisons.append({
                    'id': comp.id,
                    'manuscript1_id': comp.manuscript1_id,
                    'manuscript2_id': comp.manuscript2_id,
                    'manuscript1_name': comp.manuscript1.library_name if comp.manuscript1 else 'Unknown',
                    'manuscript2_name': comp.manuscript2.library_name if comp.manuscript2 else 'Unknown',
                    'similarity_score': comp.similarity_score,
                    'differences_count': comp.differences_count,
                    'similarities_count': comp.similarities_count,
                    'comparison_date': comp.comparison_date.isoformat(),
                    'comparison_method': comp.comparison_method,
                    'key_differences': comp.key_differences,
                    'key_similarities': comp.key_similarities
                })
            
            return {
                'id': investigation.id,
                'title': investigation.title,
                'book_title': investigation.book.title,
                'book_id': investigation.book_id,
                'description': investigation.description,
                'methodology': investigation.methodology,
                'objectives': investigation.objectives,
                'status': investigation.status,
                'start_date': investigation.start_date.isoformat() if investigation.start_date else None,
                'completion_date': investigation.completion_date.isoformat() if investigation.completion_date else None,
                'notes': investigation.notes,
                'files': files,
                'comparisons': comparisons
            }
        except Exception as e:
            logger.error(f"Failed to get investigation details: {e}")
            raise
        finally:
            self.db.close_session(session)

    def upload_file(self, investigation_id: int, file_path: str, original_filename: str, 
                   description: str = None, manuscript_id: int = None, is_primary: bool = False) -> int:
        """Upload a file to investigation"""
        def upload_file_transaction(session):
            # Validate investigation exists
            investigation = session.query(BookInvestigation).get(investigation_id)
            if not investigation:
                raise ValueError("Investigation not found")
            
            # Get file info
            file_size = os.path.getsize(file_path)
            file_type = os.path.splitext(original_filename)[1].lower().lstrip('.')
            
            # Create unique filename
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{investigation_id}_{timestamp}_{original_filename}"
            dest_path = os.path.join(self.upload_dir, unique_filename)
            
            # Copy file
            shutil.copy2(file_path, dest_path)
            
            # Create file record
            file_record = InvestigationFile(
                investigation_id=investigation_id,
                manuscript_id=manuscript_id,
                filename=unique_filename,
                original_filename=original_filename,
                file_path=dest_path,
                file_type=file_type,
                file_size=file_size,
                description=description,
                is_primary=is_primary,
                upload_date=datetime.utcnow()
            )
            
            session.add(file_record)
            session.flush()
            logger.info(f"Uploaded file: {original_filename} to investigation {investigation_id}")
            return file_record.id
        
        try:
            return self.db.execute_in_transaction(upload_file_transaction)
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise

    def delete_file(self, file_id: int) -> bool:
        """Delete a file from investigation"""
        def delete_file_transaction(session):
            file_record = session.query(InvestigationFile).get(file_id)
            if not file_record:
                raise ValueError("File not found")
            
            # Delete physical file
            try:
                if os.path.exists(file_record.file_path):
                    os.remove(file_record.file_path)
            except Exception as e:
                logger.warning(f"Failed to delete physical file: {e}")
            
            # Delete database record
            session.delete(file_record)
            logger.info(f"Deleted file: {file_record.original_filename}")
            return True
        
        try:
            return self.db.execute_in_transaction(delete_file_transaction)
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            raise

    def update_investigation(self, investigation_id: int, **kwargs) -> bool:
        """Update investigation details"""
        def update_investigation_transaction(session):
            investigation = session.query(BookInvestigation).get(investigation_id)
            if not investigation:
                raise ValueError("Investigation not found")
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(investigation, key) and value is not None:
                    setattr(investigation, key, value)
            
            # Update completion date if status changed to completed
            if kwargs.get('status') == 'completed' and investigation.status != 'completed':
                investigation.completion_date = datetime.utcnow()
            
            session.commit()
            logger.info(f"Updated investigation: {investigation.id}")
            return True
        
        try:
            return self.db.execute_in_transaction(update_investigation_transaction)
        except Exception as e:
            logger.error(f"Failed to update investigation: {e}")
            raise

    def delete_investigation(self, investigation_id: int) -> bool:
        """Delete an investigation and all its data"""
        def delete_investigation_transaction(session):
            investigation = session.query(BookInvestigation).get(investigation_id)
            if not investigation:
                raise ValueError("Investigation not found")
            
            # Delete all files
            for file_record in investigation.uploaded_files:
                try:
                    if os.path.exists(file_record.file_path):
                        os.remove(file_record.file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete physical file: {e}")
            
            # Delete investigation (cascade will handle related records)
            session.delete(investigation)
            logger.info(f"Deleted investigation: {investigation.id}")
            return True
        
        try:
            return self.db.execute_in_transaction(delete_investigation_transaction)
        except Exception as e:
            logger.error(f"Failed to delete investigation: {e}")
            raise

    def get_investigation_files(self, investigation_id: int) -> List[Dict]:
        """Get all files for an investigation"""
        session = self.db.get_session()
        try:
            files = session.query(InvestigationFile).filter(
                InvestigationFile.investigation_id == investigation_id
            ).order_by(InvestigationFile.upload_date.desc()).all()
            
            result = []
            for file in files:
                result.append({
                    'id': file.id,
                    'filename': file.original_filename or file.filename,
                    'file_type': file.file_type,
                    'file_size': file.file_size,
                    'upload_date': file.upload_date.isoformat(),
                    'description': file.description,
                    'is_primary': file.is_primary,
                    'manuscript_id': file.manuscript_id,
                    'file_path': file.file_path
                })
            
            return result
        except Exception as e:
            logger.error(f"Failed to get investigation files: {e}")
            raise
        finally:
            self.db.close_session(session)
