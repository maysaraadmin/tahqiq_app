from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table, UniqueConstraint, CheckConstraint, DateTime, Boolean
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

Base = declarative_base()

class Author(Base):
    __tablename__ = 'authors'
    __table_args__ = (
        UniqueConstraint('name', name='unique_author_name'),
        CheckConstraint('birth_year >= 0 AND birth_year <= 3000', name='check_birth_year'),
        CheckConstraint('death_year >= 0 AND death_year <= 3000', name='check_death_year'),
    )
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, unique=True)
    birth_year = Column(Integer)
    death_year = Column(Integer)
    bio = Column(Text)

    books = relationship('Book', back_populates='author', cascade='all, delete-orphan')
    # علاقات الشيوخ (التلامذة الذين تلقوا عن هذا المؤلف)
    students = relationship('SheikhRelation', foreign_keys='SheikhRelation.sheikh_id', back_populates='sheikh')
    # علاقات الطلاب (الشيوخ الذين تتلمذ عليهم هذا المؤلف)
    sheikhs = relationship('SheikhRelation', foreign_keys='SheikhRelation.student_id', back_populates='student')

class Book(Base):
    __tablename__ = 'books'
    __table_args__ = (
        UniqueConstraint('title', 'author_id', name='unique_book_title_author'),
        CheckConstraint('length(title) >= 2', name='check_title_length'),
        CheckConstraint("verification_status IN ('not_started', 'in_progress', 'verified', 'completed')", name='check_verification_status'),
    )
    
    id = Column(Integer, primary_key=True)
    title = Column(String(300), nullable=False)
    author_id = Column(Integer, ForeignKey('authors.id'), nullable=False)
    description = Column(Text)
    verification_status = Column(String(20), default='not_started')  # not_started, in_progress, verified, completed
    verification_notes = Column(Text)
    verification_date = Column(DateTime)
    is_studied = Column(Boolean, default=False)
    study_notes = Column(Text)

    author = relationship('Author', back_populates='books')
    manuscripts = relationship('Manuscript', back_populates='book', cascade='all, delete-orphan')
    study_sessions = relationship('StudySession', back_populates='book', cascade='all, delete-orphan')

class Manuscript(Base):
    __tablename__ = 'manuscripts'
    __table_args__ = (
        CheckConstraint('length(library_name) >= 2 OR library_name IS NULL', name='check_library_name'),
        CheckConstraint('length(copyist) >= 2 OR copyist IS NULL', name='check_copyist'),
    )
    
    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    library_name = Column(String(200))
    shelf_number = Column(String(100))
    copyist = Column(String(200))
    copy_date = Column(String(100))
    notes = Column(Text)

    book = relationship('Book', back_populates='manuscripts')

class SheikhRelation(Base):
    __tablename__ = 'sheikh_relations'
    __table_args__ = (
        UniqueConstraint('student_id', 'sheikh_id', name='unique_student_sheikh_relation'),
        CheckConstraint('student_id != sheikh_id', name='check_different_authors'),
        CheckConstraint('length(relation_type) >= 2 OR relation_type IS NULL OR relation_type = ""', name='check_relation_type'),
    )
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('authors.id'), nullable=False)
    sheikh_id = Column(Integer, ForeignKey('authors.id'), nullable=False)
    relation_type = Column(String(50))  # سماع، إجازة، قراءة، ...

    student = relationship('Author', foreign_keys=[student_id], back_populates='sheikhs')
    sheikh = relationship('Author', foreign_keys=[sheikh_id], back_populates='students')

class StudySession(Base):
    __tablename__ = 'study_sessions'
    __table_args__ = (
        CheckConstraint('session_date <= datetime(\'now\')', name='check_session_date'),
        CheckConstraint('duration_minutes > 0', name='check_duration'),
    )
    
    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    session_date = Column(DateTime, default=datetime.utcnow)
    duration_minutes = Column(Integer, default=60)
    pages_studied = Column(Integer)
    notes = Column(Text)
    key_findings = Column(Text)
    questions = Column(Text)
    next_steps = Column(Text)

    book = relationship('Book', back_populates='study_sessions')
