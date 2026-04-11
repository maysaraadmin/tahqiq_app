from database.db_manager import DatabaseManager
from database.models import Author, SheikhRelation
from config import config
from controllers.base_controller import BaseController
import logging
import re
import html

logger = logging.getLogger(__name__)

class AuthorController(BaseController):
    def __init__(self):
        super().__init__()
    
    def _validate_name(self, name):
        """Validate author name for security and format"""
        if not name or not isinstance(name, str):
            raise ValueError("الاسم مطلوب ويجب أن يكون نصاً")
        
        name = name.strip()
        if len(name) < 2:
            raise ValueError("الاسم يجب أن يحتوي على حرفين على الأقل")
        if len(name) > config.MAX_NAME_LENGTH:
            raise ValueError("الاسم طويل جداً")
        
        # Enhanced security: HTML escape and check for dangerous characters
        # First HTML escape to prevent XSS
        escaped_name = html.escape(name)
        if escaped_name != name:
            raise ValueError("الاسم يحتوي على أحرف HTML غير مسموحة")
        
        # Check for control characters and other dangerous patterns
        dangerous_patterns = [
            r'[<>&"\'\x00-\x1f\x7f-\x9f]',  # Control chars and HTML
            r'[\x00\x0a\x0d]',  # Null and line breaks
            r'[\uffff\ufffe]',  # Invalid Unicode
            r'[\x0b\x0c\x0e-\x1f]',  # More control chars
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, name):
                raise ValueError("الاسم يحتوي على أحرف غير مسموحة")
        
        return name
    
    def _validate_year(self, year, field_name):
        """Validate year input"""
        if year is None:
            return None
        
        if not isinstance(year, (int, str)):
            raise ValueError(f"{field_name} يجب أن يكون رقماً")
        
        try:
            year_int = int(year)
            if year_int < 0 or year_int > 3000:
                raise ValueError(f"{field_name} يجب أن يكون بين 0 و 3000")
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
            # Check for duplicate names
            existing = session.query(Author).filter(Author.name == validated_name).first()
            if existing:
                raise ValueError("المؤلف موجود مسبقاً")
            
            author = Author(name=validated_name, birth_year=validated_birth, 
                          death_year=validated_death, bio=validated_bio)
            session.add(author)
            session.flush()  # Get the ID without committing
            logger.info(f"Added author: {validated_name} (ID: {author.id})")
            return author.id
        
        # Execute in transaction with isolation
        return self.execute_in_transaction(add_author_transaction)

    def get_all_authors(self, limit=100, offset=0):
        def get_authors_transaction(session):
            # Make a copy of author data to avoid session binding issues
            authors = session.query(Author).order_by(Author.name).offset(offset).limit(limit).all()
            # Convert to simple dictionaries to avoid session binding
            author_list = []
            for author in authors:
                author_dict = {
                    'id': author.id,
                    'name': author.name,
                    'birth_year': author.birth_year,
                    'death_year': author.death_year,
                    'bio': author.bio
                }
                author_list.append(author_dict)
            return author_list
        
        try:
            return self.execute_in_transaction(get_authors_transaction)
        except Exception as e:
            logger.error(f"Failed to get authors: {e}")
            raise e
    
    def get_author_count(self):
        """Get total count of authors for pagination"""
        def count_authors_transaction(session):
            return session.query(Author).count()
        
        try:
            return self.execute_in_transaction(count_authors_transaction)
        except Exception as e:
            logger.error(f"Failed to get author count: {e}")
            raise e

    def delete_author(self, author_id):
        # Validate author_id
        validated_id = self.validate_id(author_id, "معرف المؤلف")
        
        def delete_author_transaction(session):
            author = session.query(Author).get(validated_id)
            if not author:
                raise ValueError("Author not found")
            
            author_name = author.name
            session.delete(author)
            session.flush()
            logger.info(f"Deleted author: {author_name} (ID: {validated_id})")
            return True
        
        try:
            return self.execute_in_transaction(delete_author_transaction)
        except Exception as e:
            logger.error(f"Failed to delete author {author_id}: {e}")
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
