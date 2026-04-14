from database.db_manager import DatabaseManager
from database.models import Author, SheikhRelation, Book
from config import config
from controllers.base_controller import BaseController
from utils.exception_handler import handle_exceptions, ValidationError, DatabaseError, SecurityError
import logging
import re
import html

logger = logging.getLogger(__name__)

class AuthorController(BaseController):
    def __init__(self):
        super().__init__()
    
    @handle_exceptions(default_message="Name validation failed", error_type=ValidationError)
    def _validate_name(self, name):
        """Validate author name for security and format"""
        if not name or not isinstance(name, str):
            raise ValidationError("The name is required and must be text", field="name")
        
        name = name.strip()
        if len(name) < 2:
            raise ValueError("الاسم يجب أن يحتوي على حرفين على الأقل")
        if len(name) > config.MAX_NAME_LENGTH:
            raise ValueError("الاسم طويل جداً")
        
        # Enhanced security: Check for dangerous HTML characters (allow quotes)
        dangerous_html_chars = ['<', '>', '&']
        for char in dangerous_html_chars:
            if char in name:
                raise ValueError("The name contains invalid HTML characters")
        
        # Check for control characters and other dangerous patterns
        dangerous_patterns = [
            r'[\x00-\x1f\x7f-\x9f]',  # Control chars
            r'[\x00\x0a\x0d]',  # Null and line breaks
            r'[\uffff\ufffe]',  # Invalid Unicode
            r'[\x0b\x0c\x0e-\x1f]',  # More control chars
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, name):
                raise ValueError("The name contains invalid characters")
        
        # Enhanced Unicode security validation
        try:
            # Check for dangerous Unicode categories
            import unicodedata
            
            for char in name:
                category = unicodedata.category(char)
                # Block control characters, format characters, surrogate characters, etc.
                if category in ['Cc', 'Cf', 'Cs', 'Co', 'Cn']:
                    raise ValueError(f"The name contains invalid Unicode character category: {category}")
                
                # Check for bidirectional override characters (potential security risk)
                if char in ['\u202A', '\u202B', '\u202C', '\u202D', '\u202E']:  # RLO, LRO, etc.
                    raise ValueError("The name contains bidirectional override characters")
                
                # Check for zero-width characters (potential hiding attacks)
                if char in ['\u200B', '\u200C', '\u200D', '\uFEFF']:  # ZWSP, ZWNJ, ZWJ, BOM
                    raise ValueError("The name contains zero-width characters")
            
            # Test encoding safety with multiple encodings
            encodings_to_test = ['utf-8', 'utf-16', 'utf-32']
            for encoding in encodings_to_test:
                try:
                    encoded = name.encode(encoding)
                    decoded = encoded.decode(encoding)
                    if decoded != name:
                        raise ValueError(f"Encoding mismatch detected in {encoding}")
                except (UnicodeEncodeError, UnicodeDecodeError):
                    raise ValueError(f"The name contains characters incompatible with {encoding}")
            
            # Test for normalization issues (different representations of same text)
            normalized_nfkc = unicodedata.normalize('NFKC', name)
            normalized_nfd = unicodedata.normalize('NFD', name)
            if normalized_nfkc != name or normalized_nfd != name:
                # Only allow normalization differences for Arabic diacritics
                arabic_diacritic_range = range(0x064B, 0x0653)  # Arabic diacritics range
                if not any(ord(char) in arabic_diacritic_range for char in name):
                    raise ValueError("The name contains characters with normalization issues")
            
        except ImportError:
            # Fallback to basic validation if unicodedata is not available
            pass
        except Exception as e:
            if "invalid Unicode" in str(e):
                raise
            # Re-raise Unicode-related errors
            if isinstance(e, (UnicodeEncodeError, UnicodeDecodeError)):
                raise ValueError("The name contains invalid Unicode characters")
        
        return name
    
    def _validate_year(self, year, field_name):
        """Validate year input"""
        if year is None:
            return None
        
        if not isinstance(year, (int, str)):
            raise ValueError(f"{field_name} يجب أن يكون رقماً")
        
        try:
            year_int = int(year)
            if year_int < config.MIN_YEAR or year_int > config.MAX_YEAR:
                raise ValueError(f"{field_name} يجب أن يكون بين {config.MIN_YEAR} و {config.MAX_YEAR}")
            return year_int
        except ValueError:
            raise ValueError(f"{field_name} يجب أن يكون رقماً صالحاً")
    
    def _validate_bio(self, bio):
        """Validate biography text"""
        if bio is None:
            return ''
        
        if not isinstance(bio, str):
            raise ValueError("النبذة يجب أن تكون نصاً")
        
        bio = bio.strip()
        if len(bio) > config.MAX_TEXT_LENGTH:
            raise ValueError("النبذة طويلة جداً")
        
        return bio

    def add_author(self, name, birth_year=None, death_year=None, bio=''):
        # Validate inputs
        validated_name = self._validate_name(name)
        validated_birth = self._validate_year(birth_year, "سنة الميلاد")
        validated_death = self._validate_year(death_year, "سنة الوفاة")
        validated_bio = self._validate_bio(bio)
        
        # Check logical consistency
        if validated_birth and validated_death and validated_birth > validated_death:
            raise ValueError("سنة الميلاد لا يمكن أن تكون بعد سنة الوفاة")
        
        def add_author_transaction(session):
            # Check for duplicate names (case-insensitive)
            existing = session.query(Author).filter(Author.name.ilike(validated_name)).first()
            if existing:
                raise ValueError("Author already exists")
            
            author = Author(name=validated_name, birth_year=validated_birth, 
                          death_year=validated_death, bio=validated_bio)
            session.add(author)
            session.flush()  # Get the ID without committing
            logger.info(f"Added author: {validated_name} (ID: {author.id})")
            return author.id
        
        # Execute in transaction with isolation
        return self.execute_in_transaction(add_author_transaction)

    def get_all_authors(self, limit=None, offset=0):
        """Get all authors with pagination support"""
        if limit is None:
            limit = config.DEFAULT_QUERY_LIMIT
        if limit > config.MAX_QUERY_LIMIT:
            limit = config.MAX_QUERY_LIMIT
            
        def get_authors_transaction(session):
            query = session.query(Author).offset(offset).limit(limit)
            authors = query.all()
            return [
                {
                    'id': author.id,
                    'name': author.name,
                    'birth_year': author.birth_year,
                    'death_year': author.death_year,
                    'bio': author.bio
                }
                for author in authors
            ]
        
        try:
            return self.execute_in_transaction(get_authors_transaction)
        except Exception as e:
            logger.error(f"Failed to get authors: {e}")
            raise
    
    def get_authors_count(self):
        """Get total count of authors"""
        def get_authors_count_transaction(session):
            return session.query(Author).count()
        
        try:
            return self.execute_in_transaction(get_authors_count_transaction)
        except Exception as e:
            logger.error(f"Failed to get authors count: {e}")
            raise

    def delete_author(self, author_id, cascade_delete=False):
        # Validate author_id
        validated_id = self.validate_id(author_id, "Author ID")
        
        def delete_author_transaction(session):
            # Use a single query to get author and counts efficiently
            author = session.query(Author).options(
                # Eager load related data for better performance
                session.query(Author).relationship_loader(Author.books),
                session.query(Author).relationship_loader(Author.students),
                session.query(Author).relationship_loader(Author.sheikhs)
            ).get(validated_id)
            
            if not author:
                raise ValueError("Author not found")
            
            author_name = author.name
            
            # Use efficient bulk count queries
            from sqlalchemy import func, or_
            
            # Get all dependency counts in a single query
            dependency_counts = session.query(
                func.count(Book.id).label('books'),
                func.count(SheikhRelation.id).filter(SheikhRelation.sheikh_id == validated_id).label('sheikh_relations'),
                func.count(SheikhRelation.id).filter(SheikhRelation.student_id == validated_id).label('student_relations')
            ).outerjoin(Book, Book.author_id == Author.id).outerjoin(
                SheikhRelation, or_(SheikhRelation.sheikh_id == validated_id, SheikhRelation.student_id == validated_id)
            ).filter(Author.id == validated_id).first()
            
            book_count = dependency_counts.books or 0
            sheikh_relations = dependency_counts.sheikh_relations or 0
            student_relations = dependency_counts.student_relations or 0
            total_relations = sheikh_relations + student_relations
            
            # If cascade_delete is False and there are dependencies, raise error
            if not cascade_delete and (book_count > 0 or total_relations > 0):
                dependencies = []
                if book_count > 0:
                    dependencies.append(f"{book_count} book(s)")
                if sheikh_relations > 0:
                    dependencies.append(f"{sheikh_relations} student relation(s)")
                if student_relations > 0:
                    dependencies.append(f"{student_relations} teacher relation(s)")
                
                raise ValueError(f"Cannot delete author '{author_name}' - linked to: {', '.join(dependencies)}. Use cascade delete to remove all linked data.")
            
            # If cascade_delete is True, use efficient bulk operations
            if cascade_delete:
                # Use bulk delete for books (more efficient than individual deletes)
                if book_count > 0:
                    deleted_books = session.query(Book).filter(Book.author_id == validated_id).delete(synchronize_session=False)
                    logger.info(f"Deleted {deleted_books} books linked to author '{author_name}'")
                
                # Use bulk delete for relations
                if total_relations > 0:
                    # Delete all relations in a single query
                    deleted_relations = session.query(SheikhRelation).filter(
                        or_(SheikhRelation.sheikh_id == validated_id, SheikhRelation.student_id == validated_id)
                    ).delete(synchronize_session=False)
                    logger.info(f"Deleted {deleted_relations} relations linked to author '{author_name}'")
            
            # Finally delete the author
            session.delete(author)
            session.flush()
            logger.info(f"Deleted author: {author_name} (ID: {validated_id})")
            return True
        
        try:
            return self.execute_in_transaction(delete_author_transaction)
        except Exception as e:
            logger.error(f"Failed to delete author {author_id}: {e}")
            raise e

    def update_author(self, author_id, name=None, birth_year=None, death_year=None, bio=None):
        """Update an existing author with validation"""
        # Validate author_id
        validated_id = self.validate_id(author_id, "Author ID")
        
        def update_author_transaction(session):
            # Get the existing author
            author = session.query(Author).get(validated_id)
            if not author:
                raise ValueError("Author not found")
            
            # Update fields only if they are provided
            if name is not None:
                validated_name = self._validate_name(name)
                # Check for duplicate names (case-insensitive, excluding current author)
                existing = session.query(Author).filter(
                    Author.name.ilike(validated_name),
                    Author.id != validated_id
                ).first()
                if existing:
                    raise ValueError("Author with this name already exists")
                author.name = validated_name
            
            if birth_year is not None:
                validated_birth = self._validate_year(birth_year, "Birth Year")
                author.birth_year = validated_birth
            
            if death_year is not None:
                validated_death = self._validate_year(death_year, "Death Year")
                author.death_year = validated_death
            
            if bio is not None:
                validated_bio = self._validate_bio(bio)
                author.bio = validated_bio
            
            # Check logical consistency
            if author.birth_year and author.death_year and author.birth_year > author.death_year:
                raise ValueError("Birth year cannot be after death year")
            
            session.flush()
            logger.info(f"Updated author: {author.name} (ID: {author.id})")
            return True
        
        try:
            return self.execute_in_transaction(update_author_transaction)
        except Exception as e:
            logger.error(f"Failed to update author {author_id}: {e}")
            raise e

    def add_sheikh_relation(self, student_id, sheikh_id, relation_type=''):
        # Validate inputs
        validated_student_id = self.validate_id(student_id, "معرف الطالب")
        validated_sheikh_id = self.validate_id(sheikh_id, "معرف الشيخ")
        
        if validated_student_id == validated_sheikh_id:
            raise ValueError("لا يمكن إضافة علاقة بين نفس الشخص")
        
        if relation_type and not isinstance(relation_type, str):
            raise ValueError("نوع العلاقة يجب أن يكون نصاً")
        
        if relation_type and len(relation_type) > 50:
            raise ValueError("نوع العلاقة طويل جداً")
        
        def add_relation_transaction(session):
            # Check if both authors exist
            student = session.query(Author).get(validated_student_id)
            sheikh = session.query(Author).get(validated_sheikh_id)
            
            if not student or not sheikh:
                raise ValueError("One of the authors does not exist")
            
            # Check for duplicate relation
            existing = session.query(SheikhRelation).filter(
                SheikhRelation.student_id == validated_student_id,
                SheikhRelation.sheikh_id == validated_sheikh_id
            ).first()
            
            if existing:
                raise ValueError("Relation already exists")
            
            rel = SheikhRelation(student_id=validated_student_id, sheikh_id=validated_sheikh_id, relation_type=relation_type or '')
            session.add(rel)
            session.flush()
            # Log before accessing relationships to avoid session binding issues
            student_name = student.name
            sheikh_name = sheikh.name
            logger.info(f"Added relation: {student_name} -> {sheikh_name} ({relation_type or 'undefined'})")
            return rel.id
        
        try:
            return self.execute_in_transaction(add_relation_transaction)
        except Exception as e:
            logger.error(f"Failed to add sheikh relation: {e}")
            raise e
