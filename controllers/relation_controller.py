from database.db_manager import DatabaseManager
from database.models import SheikhRelation, Author
import logging

logger = logging.getLogger(__name__)

class RelationController:
    def __init__(self):
        self.db = DatabaseManager()

    def get_author_relations(self, author_id):
        """Get all relations for a specific author with validation"""
        # Validate author_id
        try:
            author_id = int(author_id)
            if author_id <= 0:
                raise ValueError("Invalid author ID")
        except (ValueError, TypeError):
            raise ValueError("Author ID must be a positive integer")
        
        session = self.db.get_session()
        try:
            author = session.query(Author).get(author_id)
            if not author:
                raise ValueError("Author not found")
            
            relations = []
            # Shuyukh (those this author learned from)
            for rel in author.sheikhs:
                relations.append({
                    'type': 'sheikh',
                    'name': rel.sheikh.name,
                    'relation_type': rel.relation_type or '',
                    'id': rel.id,
                    'related_id': rel.sheikh.id
                })
            # Students (those who learned from this author)
            for rel in author.students:
                relations.append({
                    'type': 'student',
                    'name': rel.student.name,
                    'relation_type': rel.relation_type or '',
                    'id': rel.id,
                    'related_id': rel.student.id
                })
            
            logger.debug(f"Found {len(relations)} relations for author {author_id}")
            return relations
        except Exception as e:
            logger.error(f"Failed to get relations for author {author_id}: {e}")
            raise
        finally:
            self.db.close_session(session)

    def delete_relation(self, relation_id):
        """Delete a relation with validation"""
        # Validate relation_id
        try:
            relation_id = int(relation_id)
            if relation_id <= 0:
                raise ValueError("Invalid relation ID")
        except (ValueError, TypeError):
            raise ValueError("Relation ID must be a positive integer")
        
        session = self.db.get_session()
        try:
            relation = session.query(SheikhRelation).get(relation_id)
            if not relation:
                raise ValueError("Relation not found")
            
            # Log the deletion
            student_name = relation.student.name if relation.student else "Unknown"
            sheikh_name = relation.sheikh.name if relation.sheikh else "Unknown"
            
            session.delete(relation)
            session.commit()
            
            logger.info(f"Deleted relation: {student_name} -> {sheikh_name}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete relation {relation_id}: {e}")
            raise
        finally:
            self.db.close_session(session)

    def get_relation_count(self, author_id=None):
        """Get total count of relations, optionally filtered by author"""
        session = self.db.get_session()
        try:
            query = session.query(SheikhRelation)
            if author_id:
                query = query.filter(
                    (SheikhRelation.student_id == author_id) |
                    (SheikhRelation.sheikh_id == author_id)
                )
            return query.count()
        except Exception as e:
            logger.error(f"Failed to get relation count: {e}")
            raise
        finally:
            self.db.close_session(session)

    def get_all_relations(self, limit=100, offset=0):
        """Get all relations with pagination"""
        session = self.db.get_session()
        try:
            relations = session.query(SheikhRelation).offset(offset).limit(limit).all()
            result = []
            for rel in relations:
                result.append({
                    'id': rel.id,
                    'student_id': rel.student_id,
                    'sheikh_id': rel.sheikh_id,
                    'student_name': rel.student.name if rel.student else 'Unknown',
                    'sheikh_name': rel.sheikh.name if rel.sheikh else 'Unknown',
                    'relation_type': rel.relation_type or ''
                })
            return result
        except Exception as e:
            logger.error(f"Failed to get all relations: {e}")
            raise
        finally:
            self.db.close_session(session)

    def update_relation(self, relation_id, student_id=None, sheikh_id=None, relation_type=None):
        """Update an existing relation with validation"""
        # Validate relation_id
        try:
            relation_id = int(relation_id)
            if relation_id <= 0:
                raise ValueError("Invalid relation ID")
        except (ValueError, TypeError):
            raise ValueError("Relation ID must be a positive integer")
        
        session = self.db.get_session()
        try:
            relation = session.query(SheikhRelation).get(relation_id)
            if not relation:
                raise ValueError("Relation not found")
            
            # Update fields only if they are provided
            if student_id is not None:
                try:
                    student_id = int(student_id)
                    if student_id <= 0:
                        raise ValueError("Invalid student ID")
                except (ValueError, TypeError):
                    raise ValueError("Student ID must be a positive integer")
                
                # Check if student exists
                student = session.query(Author).get(student_id)
                if not student:
                    raise ValueError("Student author not found")
                
                # Prevent self-relation if sheikh_id is also being updated
                if sheikh_id is not None and student_id == int(sheikh_id):
                    raise ValueError("Cannot create relation between same author")
                elif sheikh_id is None and student_id == relation.sheikh_id:
                    raise ValueError("Cannot create relation between same author")
                
                relation.student_id = student_id
            
            if sheikh_id is not None:
                try:
                    sheikh_id = int(sheikh_id)
                    if sheikh_id <= 0:
                        raise ValueError("Invalid sheikh ID")
                except (ValueError, TypeError):
                    raise ValueError("Sheikh ID must be a positive integer")
                
                # Check if sheikh exists
                sheikh = session.query(Author).get(sheikh_id)
                if not sheikh:
                    raise ValueError("Sheikh author not found")
                
                # Prevent self-relation if student_id is also being updated
                if student_id is not None and int(student_id) == sheikh_id:
                    raise ValueError("Cannot create relation between same author")
                elif student_id is None and relation.student_id == sheikh_id:
                    raise ValueError("Cannot create relation between same author")
                
                relation.sheikh_id = sheikh_id
            
            if relation_type is not None:
                if not isinstance(relation_type, str):
                    raise ValueError("Relation type must be a string")
                if len(relation_type) > 50:
                    raise ValueError("Relation type is too long")
                relation.relation_type = relation_type
            
            # Check for duplicate relation
            existing = session.query(SheikhRelation).filter(
                SheikhRelation.student_id == relation.student_id,
                SheikhRelation.sheikh_id == relation.sheikh_id,
                SheikhRelation.id != relation_id
            ).first()
            
            if existing:
                raise ValueError("Relation already exists")
            
            session.commit()
            logger.info(f"Updated relation: {relation.student_id} -> {relation.sheikh_id} ({relation.relation_type or 'undefined'})")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update relation {relation_id}: {e}")
            raise
        finally:
            self.db.close_session(session)
