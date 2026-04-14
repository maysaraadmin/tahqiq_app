from controllers.base_controller import BaseController
from database.models import BookIsnad, IsnadChain, Book
from database.db_manager import DatabaseManager
from datetime import datetime
import os
import shutil
import logging

logger = logging.getLogger(__name__)

class IsnadController(BaseController):
    def __init__(self):
        super().__init__()
        self.upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'isnad_books')
        os.makedirs(self.upload_dir, exist_ok=True)

    def create_isnad(self, book_id, file_path, isnad_chain):
        """Create new book isnad with chain"""
        def create_isnad_transaction(session):
            # Validate book exists
            book = session.query(Book).get(book_id)
            if not book:
                raise ValueError("Book not found")
            
            # Upload file
            filename = os.path.basename(file_path)
            file_ext = os.path.splitext(filename)[1]
            new_filename = f"book_{book_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_ext}"
            upload_path = os.path.join(self.upload_dir, new_filename)
            
            # Copy file to upload directory
            shutil.copy2(file_path, upload_path)
            
            # Create isnad record
            isnad = BookIsnad(
                book_id=book_id,
                file_path=upload_path,
                original_filename=filename,
                upload_date=datetime.now(),
                status='active'
            )
            
            session.add(isnad)
            session.flush()  # Get the ID
            
            # Create isnad chain records
            for sheikh_data in isnad_chain:
                chain_record = IsnadChain(
                    isnad_id=isnad.id,
                    sheikh_name=sheikh_data['name'],
                    sheikh_description=sheikh_data.get('description', ''),
                    chain_order=sheikh_data['order']
                )
                session.add(chain_record)
            
            logger.info(f"Created isnad for book {book_id} with {len(isnad_chain)} chain members")
            return isnad.id
        
        try:
            return self.execute_in_transaction(create_isnad_transaction)
        except Exception as e:
            logger.error(f"Failed to create isnad: {e}")
            raise e

    def get_book_isnads(self, book_id):
        """Get all isnads for a book"""
        def get_isnads_transaction(session):
            isnads = session.query(BookIsnad).filter(BookIsnad.book_id == book_id).all()
            
            result = []
            for isnad in isnads:
                # Get chain members
                chain = session.query(IsnadChain).filter(
                    IsnadChain.isnad_id == isnad.id
                ).order_by(IsnadChain.chain_order).all()
                
                chain_data = []
                for member in chain:
                    chain_data.append({
                        'id': member.id,
                        'sheikh_name': member.sheikh_name,
                        'sheikh_description': member.sheikh_description,
                        'chain_order': member.chain_order
                    })
                
                result.append({
                    'id': isnad.id,
                    'book_id': isnad.book_id,
                    'file_path': isnad.file_path,
                    'original_filename': isnad.original_filename,
                    'upload_date': isnad.upload_date.isoformat() if isnad.upload_date else None,
                    'status': isnad.status,
                    'chain': chain_data,
                    'chain_count': len(chain_data)
                })
            
            return result
        
        try:
            return self.execute_in_transaction(get_isnads_transaction)
        except Exception as e:
            logger.error(f"Failed to get book isnads: {e}")
            raise e

    def get_all_isnads(self):
        """Get all isnads with book information"""
        def get_all_transaction(session):
            isnads = session.query(BookIsnad).all()
            
            result = []
            for isnad in isnads:
                # Get book information
                book = session.query(Book).get(isnad.book_id)
                
                # Get chain members
                chain = session.query(IsnadChain).filter(
                    IsnadChain.isnad_id == isnad.id
                ).order_by(IsnadChain.chain_order).all()
                
                chain_data = []
                for member in chain:
                    chain_data.append({
                        'id': member.id,
                        'sheikh_name': member.sheikh_name,
                        'sheikh_description': member.sheikh_description,
                        'chain_order': member.chain_order
                    })
                
                result.append({
                    'id': isnad.id,
                    'book_id': isnad.book_id,
                    'book_title': book.title if book else 'Unknown',
                    'author_name': book.author.name if book and book.author else 'Unknown',
                    'file_path': isnad.file_path,
                    'original_filename': isnad.original_filename,
                    'upload_date': isnad.upload_date.isoformat() if isnad.upload_date else None,
                    'status': isnad.status,
                    'chain': chain_data,
                    'chain_count': len(chain_data)
                })
            
            return result
        
        try:
            return self.execute_in_transaction(get_all_transaction)
        except Exception as e:
            logger.error(f"Failed to get all isnads: {e}")
            raise e

    def get_isnad_details(self, isnad_id):
        """Get detailed information about a specific isnad"""
        def get_details_transaction(session):
            isnad = session.query(BookIsnad).get(isnad_id)
            if not isnad:
                raise ValueError("Isnad not found")
            
            # Get book information
            book = session.query(Book).get(isnad.book_id)
            
            # Get chain members
            chain = session.query(IsnadChain).filter(
                IsnadChain.isnad_id == isnad.id
            ).order_by(IsnadChain.chain_order).all()
            
            chain_data = []
            for member in chain:
                chain_data.append({
                    'id': member.id,
                    'sheikh_name': member.sheikh_name,
                    'sheikh_description': member.sheikh_description,
                    'chain_order': member.chain_order
                })
            
            return {
                'id': isnad.id,
                'book_id': isnad.book_id,
                'book_title': book.title if book else 'Unknown',
                'author_name': book.author.name if book and book.author else 'Unknown',
                'book_description': book.description if book else '',
                'file_path': isnad.file_path,
                'original_filename': isnad.original_filename,
                'upload_date': isnad.upload_date.isoformat() if isnad.upload_date else None,
                'status': isnad.status,
                'chain': chain_data,
                'chain_count': len(chain_data)
            }
        
        try:
            return self.execute_in_transaction(get_details_transaction)
        except Exception as e:
            logger.error(f"Failed to get isnad details: {e}")
            raise e

    def update_isnad(self, isnad_id, status=None):
        """Update isnad status"""
        def update_transaction(session):
            isnad = session.query(BookIsnad).get(isnad_id)
            if not isnad:
                raise ValueError("Isnad not found")
            
            if status is not None:
                isnad.status = status
            
            session.flush()
            logger.info(f"Updated isnad {isnad_id}")
            return True
        
        try:
            return self.execute_in_transaction(update_transaction)
        except Exception as e:
            logger.error(f"Failed to update isnad: {e}")
            raise e

    def delete_isnad(self, isnad_id):
        """Delete isnad and associated files"""
        def delete_transaction(session):
            isnad = session.query(BookIsnad).get(isnad_id)
            if not isnad:
                raise ValueError("Isnad not found")
            
            # Delete file if exists
            if isnad.file_path and os.path.exists(isnad.file_path):
                try:
                    os.remove(isnad.file_path)
                    logger.info(f"Deleted file: {isnad.file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete file {isnad.file_path}: {e}")
            
            # Delete chain records (cascade should handle this)
            session.delete(isnad)
            session.flush()
            logger.info(f"Deleted isnad {isnad_id}")
            return True
        
        try:
            return self.execute_in_transaction(delete_transaction)
        except Exception as e:
            logger.error(f"Failed to delete isnad: {e}")
            raise e

    def get_isnad_file_path(self, isnad_id):
        """Get the file path for an isnad"""
        def get_path_transaction(session):
            isnad = session.query(BookIsnad).get(isnad_id)
            if not isnad:
                raise ValueError("Isnad not found")
            
            return isnad.file_path
        
        try:
            return self.execute_in_transaction(get_path_transaction)
        except Exception as e:
            logger.error(f"Failed to get isnad file path: {e}")
            raise e

    def search_isnads(self, query):
        """Search isnads by book title, author name, or sheikh name"""
        def search_transaction(session):
            # Search in books
            books = session.query(Book).filter(
                Book.title.contains(query) |
                Book.description.contains(query)
            ).all()
            
            book_ids = [book.id for book in books]
            
            # Search in isnad chain
            chain_members = session.query(IsnadChain).filter(
                IsnadChain.sheikh_name.contains(query) |
                IsnadChain.sheikh_description.contains(query)
            ).all()
            
            isnad_ids = list(set([member.isnad_id for member in chain_members]))
            
            # Combine results
            all_isnad_ids = list(set(book_ids + isnad_ids))
            
            isnads = session.query(BookIsnad).filter(
                BookIsnad.id.in_(all_isnad_ids)
            ).all()
            
            result = []
            for isnad in isnads:
                book = session.query(Book).get(isnad.book_id)
                
                result.append({
                    'id': isnad.id,
                    'book_id': isnad.book_id,
                    'book_title': book.title if book else 'Unknown',
                    'author_name': book.author.name if book and book.author else 'Unknown',
                    'original_filename': isnad.original_filename,
                    'upload_date': isnad.upload_date.isoformat() if isnad.upload_date else None,
                    'status': isnad.status
                })
            
            return result
        
        try:
            return self.execute_in_transaction(search_transaction)
        except Exception as e:
            logger.error(f"Failed to search isnads: {e}")
            raise e
