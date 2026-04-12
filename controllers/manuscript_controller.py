from controllers.base_controller import BaseController
from database.models import Manuscript, Book
import logging

logger = logging.getLogger(__name__)

class ManuscriptController(BaseController):
    def __init__(self):
        super().__init__()
    
    def add_manuscript(self, book_id, library_name, shelf_number, copyist=None, copy_date=None, notes=None):
        """Add a new manuscript copy for a book"""
        def add_manuscript_transaction(session):
            # Validate book exists
            book = session.query(Book).get(book_id)
            if not book:
                raise ValueError("Book not found")
            
            # Validate required fields
            if not library_name or not library_name.strip():
                raise ValueError("Library name is required")
            if not shelf_number or not shelf_number.strip():
                raise ValueError("Shelf number is required")
            
            # Check for duplicates
            existing = session.query(Manuscript).filter(
                Manuscript.book_id == book_id,
                Manuscript.library_name == library_name.strip(),
                Manuscript.shelf_number == shelf_number.strip()
            ).first()
            
            if existing:
                raise ValueError("A manuscript with this library and shelf number already exists for this book")
            
            # Create manuscript
            manuscript = Manuscript(
                book_id=book_id,
                library_name=library_name.strip(),
                shelf_number=shelf_number.strip(),
                copyist=copyist.strip() if copyist else None,
                copy_date=copy_date.strip() if copy_date else None,
                notes=notes.strip() if notes else None
            )
            
            session.add(manuscript)
            session.flush()
            logger.info(f"Added manuscript for book '{book.title}' at {library_name} (ID: {manuscript.id})")
            return manuscript.id
        
        return self.execute_in_transaction(add_manuscript_transaction)
    
    def get_book_manuscripts(self, book_id):
        """Get all manuscripts for a specific book"""
        def get_manuscripts_transaction(session):
            # Validate book exists
            book = session.query(Book).get(book_id)
            if not book:
                raise ValueError("Book not found")
            
            manuscripts = session.query(Manuscript).filter(
                Manuscript.book_id == book_id
            ).order_by(Manuscript.library_name, Manuscript.shelf_number).all()
            
            return [
                {
                    'id': manuscript.id,
                    'book_id': manuscript.book_id,
                    'book_title': book.title,
                    'library_name': manuscript.library_name,
                    'shelf_number': manuscript.shelf_number,
                    'copyist': manuscript.copyist,
                    'copy_date': manuscript.copy_date,
                    'notes': manuscript.notes
                }
                for manuscript in manuscripts
            ]
        
        return self.execute_in_transaction(get_manuscripts_transaction)
    
    def get_all_manuscripts(self, limit=100, offset=0):
        """Get all manuscripts with book information"""
        def get_manuscripts_transaction(session):
            manuscripts = session.query(Manuscript, Book).join(Book).order_by(
                Book.title, Manuscript.library_name, Manuscript.shelf_number
            ).offset(offset).limit(limit).all()
            
            return [
                {
                    'id': manuscript.id,
                    'book_id': manuscript.book_id,
                    'book_title': book.title,
                    'library_name': manuscript.library_name,
                    'shelf_number': manuscript.shelf_number,
                    'copyist': manuscript.copyist,
                    'copy_date': manuscript.copy_date,
                    'notes': manuscript.notes
                }
                for manuscript, book in manuscripts
            ]
        
        return self.execute_in_transaction(get_manuscripts_transaction)
    
    def update_manuscript(self, manuscript_id, library_name=None, shelf_number=None, copyist=None, copy_date=None, notes=None):
        """Update an existing manuscript"""
        def update_manuscript_transaction(session):
            manuscript = session.query(Manuscript).get(manuscript_id)
            if not manuscript:
                raise ValueError("Manuscript not found")
            
            # Update fields if provided
            if library_name is not None:
                if not library_name or not library_name.strip():
                    raise ValueError("Library name is required")
                manuscript.library_name = library_name.strip()
            
            if shelf_number is not None:
                if not shelf_number or not shelf_number.strip():
                    raise ValueError("Shelf number is required")
                manuscript.shelf_number = shelf_number.strip()
            
            if copyist is not None:
                manuscript.copyist = copyist.strip() if copyist else None
            
            if copy_date is not None:
                manuscript.copy_date = copy_date.strip() if copy_date else None
            
            if notes is not None:
                manuscript.notes = notes.strip() if notes else None
            
            session.flush()
            logger.info(f"Updated manuscript (ID: {manuscript_id})")
            return True
        
        return self.execute_in_transaction(update_manuscript_transaction)
    
    def delete_manuscript(self, manuscript_id):
        """Delete a manuscript"""
        def delete_manuscript_transaction(session):
            manuscript = session.query(Manuscript).get(manuscript_id)
            if not manuscript:
                raise ValueError("Manuscript not found")
            
            manuscript_info = f"{manuscript.library_name} - {manuscript.shelf_number}"
            session.delete(manuscript)
            session.commit()
            logger.info(f"Deleted manuscript: {manuscript_info} (ID: {manuscript_id})")
            return True
        
        return self.execute_in_transaction(delete_manuscript_transaction)
    
    def get_manuscript_count(self):
        """Get total count of manuscripts"""
        def count_manuscripts_transaction(session):
            return session.query(Manuscript).count()
        
        return self.execute_in_transaction(count_manuscripts_transaction)
    
    def search_manuscripts(self, query, limit=50):
        """Search manuscripts by library name, shelf number, or book title"""
        def search_manuscripts_transaction(session):
            search_term = f"%{query}%"
            manuscripts = session.query(Manuscript, Book).join(Book).filter(
                (Manuscript.library_name.ilike(search_term)) |
                (Manuscript.shelf_number.ilike(search_term)) |
                (Book.title.ilike(search_term))
            ).order_by(Book.title, Manuscript.library_name).limit(limit).all()
            
            return [
                {
                    'id': manuscript.id,
                    'book_id': manuscript.book_id,
                    'book_title': book.title,
                    'library_name': manuscript.library_name,
                    'shelf_number': manuscript.shelf_number,
                    'copyist': manuscript.copyist,
                    'copy_date': manuscript.copy_date,
                    'notes': manuscript.notes
                }
                for manuscript, book in manuscripts
            ]
        
        return self.execute_in_transaction(search_manuscripts_transaction)
