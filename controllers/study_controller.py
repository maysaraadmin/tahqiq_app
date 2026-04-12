from database.db_manager import DatabaseManager
from database.models import StudySession, Book
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class StudyController:
    def __init__(self):
        self.db = DatabaseManager()
    
    def create_study_session(self, book_id, duration_minutes=60, pages_studied=None, notes=None, 
                           key_findings=None, questions=None, next_steps=None):
        """Create a new study session for a book"""
        def create_session_transaction(session):
            # Validate book exists
            book = session.query(Book).get(book_id)
            if not book:
                raise ValueError("Book not found")
            
            # Create study session
            study_session = StudySession(
                book_id=book_id,
                session_date=datetime.utcnow(),
                duration_minutes=duration_minutes,
                pages_studied=pages_studied,
                notes=notes,
                key_findings=key_findings,
                questions=questions,
                next_steps=next_steps
            )
            
            session.add(study_session)
            session.flush()
            
            # Update book study status
            if not book.is_studied:
                book.is_studied = True
                if not book.study_notes:
                    book.study_notes = f"First study session on {study_session.session_date.strftime('%Y-%m-%d')}"
            
            logger.info(f"Created study session for book '{book.title}' (ID: {book.id})")
            return study_session.id
        
        return self.db.execute_in_transaction(create_session_transaction)
    
    def get_book_study_sessions(self, book_id):
        """Get all study sessions for a book"""
        def get_sessions_transaction(session):
            sessions = session.query(StudySession).filter(
                StudySession.book_id == book_id
            ).order_by(StudySession.session_date.desc()).all()
            
            return [
                {
                    'id': session.id,
                    'book_id': session.book_id,
                    'session_date': session.session_date,
                    'duration_minutes': session.duration_minutes,
                    'pages_studied': session.pages_studied,
                    'notes': session.notes,
                    'key_findings': session.key_findings,
                    'questions': session.questions,
                    'next_steps': session.next_steps
                }
                for session in sessions
            ]
        
        return self.db.execute_in_transaction(get_sessions_transaction)
    
    def update_book_verification_status(self, book_id, status, notes=None):
        """Update book verification status"""
        def update_verification_transaction(session):
            book = session.query(Book).get(book_id)
            if not book:
                raise ValueError("Book not found")
            
            valid_statuses = ['not_started', 'in_progress', 'verified', 'completed']
            if status not in valid_statuses:
                raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
            
            book.verification_status = status
            if status in ['verified', 'completed']:
                book.verification_date = datetime.utcnow()
            
            if notes:
                book.verification_notes = notes
            
            logger.info(f"Updated book '{book.title}' verification status to '{status}'")
            return True
        
        return self.db.execute_in_transaction(update_verification_transaction)
    
    def get_author_study_summary(self, author_id):
        """Get study summary for an author including their books"""
        def get_summary_transaction(session):
            # Get author's books with their study status
            books = session.query(Book).filter(Book.author_id == author_id).all()
            
            summary = {
                'total_books': len(books),
                'studied_books': sum(1 for book in books if book.is_studied),
                'verified_books': sum(1 for book in books if book.verification_status == 'verified'),
                'completed_books': sum(1 for book in books if book.verification_status == 'completed'),
                'books': []
            }
            
            for book in books:
                # Count study sessions for this book
                session_count = session.query(StudySession).filter(
                    StudySession.book_id == book.id
                ).count()
                
                summary['books'].append({
                    'id': book.id,
                    'title': book.title,
                    'verification_status': book.verification_status,
                    'is_studied': book.is_studied,
                    'study_sessions_count': session_count,
                    'verification_date': book.verification_date
                })
            
            return summary
        
        return self.db.execute_in_transaction(get_summary_transaction)
    
    def get_study_statistics(self):
        """Get overall study statistics"""
        def get_stats_transaction(session):
            total_books = session.query(Book).count()
            studied_books = session.query(Book).filter(Book.is_studied == True).count()
            verified_books = session.query(Book).filter(Book.verification_status == 'verified').count()
            completed_books = session.query(Book).filter(Book.verification_status == 'completed').count()
            total_sessions = session.query(StudySession).count()
            
            return {
                'total_books': total_books,
                'studied_books': studied_books,
                'verified_books': verified_books,
                'completed_books': completed_books,
                'total_study_sessions': total_sessions,
                'study_progress': round((studied_books / total_books * 100) if total_books > 0 else 0, 2),
                'verification_progress': round((verified_books / total_books * 100) if total_books > 0 else 0, 2)
            }
        
        return self.db.execute_in_transaction(get_stats_transaction)
