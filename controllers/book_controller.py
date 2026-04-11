from database.db_manager import DatabaseManager
from database.models import Book, Author
from config import config
from controllers.base_controller import BaseController
import logging
import re
import html

logger = logging.getLogger(__name__)

class BookController(BaseController):
    def __init__(self):
        super().__init__()
    
    def _validate_title(self, title):
        """Validate book title for security and format"""
        if not title or not isinstance(title, str):
            raise ValueError("العنوان مطلوب ويجب أن يكون نصاً")
        
        title = title.strip()
        if len(title) < 2:
            raise ValueError("العنوان يجب أن يحتوي على حرفين على الأقل")
        if len(title) > config.MAX_TITLE_LENGTH:
            raise ValueError("العنوان طويل جداً")
        
        # Enhanced security: HTML escape and check for dangerous characters
        escaped_title = html.escape(title)
        if escaped_title != title:
            raise ValueError("العنوان يحتوي على أحرف HTML غير مسموحة")
        
        # Check for dangerous patterns
        dangerous_patterns = [
            r'[<>&"\'\x00-\x1f\x7f-\x9f]',
            r'[\x00\x0a\x0d]',
            r'[\uffff\ufffe]',
            r'[\x0b\x0c\x0e-\x1f]',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, title):
                raise ValueError("العنوان يحتوي على أحرف غير مسموحة")
        
        return title
    
    def _validate_description(self, description):
        """Validate book description"""
        if description is None:
            return ''
        
        if not isinstance(description, str):
            raise ValueError("الوصف يجب أن يكون نصاً")
        
        description = description.strip()
        if len(description) > config.MAX_TEXT_LENGTH:
            raise ValueError("الوصف طويل جداً")
        
        return description

    def add_book(self, title, author_id, description=''):
        # Validate inputs
        validated_title = self._validate_title(title)
        validated_description = self._validate_description(description)
        
        # Validate author_id
        validated_author_id = self.validate_id(author_id, "Author ID")
        
        def add_book_transaction(session):
            # Check if author exists
            author = session.query(Author).get(validated_author_id)
            if not author:
                raise ValueError("Author not found")
            
            # Check for duplicate titles by same author
            existing = session.query(Book).filter(
                Book.title == validated_title,
                Book.author_id == validated_author_id
            ).first()
            
            if existing:
                raise ValueError("Book with this title already exists for this author")
            
            book = Book(title=validated_title, author_id=validated_author_id, description=validated_description)
            session.add(book)
            session.flush()
            logger.info(f"Added book: {validated_title} by {author.name} (ID: {book.id})")
            return book.id
        
        try:
            return self.execute_in_transaction(add_book_transaction)
        except Exception as e:
            logger.error(f"Failed to add book: {e}")
            raise

    def get_all_books(self, limit=100, offset=0):
        def get_books_transaction(session):
            # Include author information to prevent lazy loading issues
            from sqlalchemy.orm import joinedload
            books = session.query(Book).options(joinedload(Book.author)).order_by(Book.title).offset(offset).limit(limit).all()
            return books
        
        try:
            return self.execute_in_transaction(get_books_transaction)
        except Exception as e:
            logger.error(f"Failed to get books: {e}")
            raise e
    
    def get_book_count(self):
        """Get total count of books for pagination"""
        def count_books_transaction(session):
            return session.query(Book).count()
        
        try:
            return self.execute_in_transaction(count_books_transaction)
        except Exception as e:
            logger.error(f"Failed to get book count: {e}")
            raise e

    def delete_book(self, book_id):
        # Validate book_id
        try:
            book_id = int(book_id)
            if book_id <= 0:
                raise ValueError("معرف الكتاب غير صالح")
        except (ValueError, TypeError):
            raise ValueError("معرف الكتاب يجب أن يكون رقماً")
        
        session = self.db.get_session()
        try:
            book = session.query(Book).get(book_id)
            if not book:
                raise ValueError("الكتاب غير موجود")
            
            book_title = book.title
            session.delete(book)
            session.commit()
            logger.info(f"Deleted book: {book_title} (ID: {book_id})")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete book {book_id}: {e}")
            raise e
        finally:
            self.db.close_session()
