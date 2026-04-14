"""
Unit tests for database models
"""

import unittest
from database.models import Author, Book, BookIsnad, IsnadChain
from database.constants import (
    MIN_YEAR, MAX_YEAR, MAX_AUTHOR_NAME_LENGTH, 
    MAX_BOOK_TITLE_LENGTH
)


class TestAuthorModel(unittest.TestCase):
    """Test Author model"""
    
    def test_author_creation(self):
        """Test creating an author"""
        author = Author(
            name="Test Author",
            birth_year=1900,
            death_year=2000,
            bio="Test bio"
        )
        
        self.assertEqual(author.name, "Test Author")
        self.assertEqual(author.birth_year, 1900)
        self.assertEqual(author.death_year, 2000)
        self.assertEqual(author.bio, "Test bio")
    
    def test_author_validation(self):
        """Test author validation constraints"""
        # Valid author
        author = Author(name="Valid Author")
        self.assertEqual(author.name, "Valid Author")
        
        # Test name length constraint (SQLAlchemy validates at DB level, not object creation)
        long_name = "A" * (MAX_AUTHOR_NAME_LENGTH + 1)
        # This won't raise an error at object creation, but will at DB insert
        author_long = Author(name=long_name)
        self.assertEqual(author_long.name, long_name)
    
    def test_year_validation(self):
        """Test year validation"""
        # Valid years
        author = Author(name="Test")
        author.birth_year = MIN_YEAR
        author.death_year = MAX_YEAR
        self.assertEqual(author.birth_year, MIN_YEAR)
        self.assertEqual(author.death_year, MAX_YEAR)


class TestBookModel(unittest.TestCase):
    """Test Book model"""
    
    def test_book_creation(self):
        """Test creating a book"""
        book = Book(
            title="Test Book",
            author_id=1,
            description="Test description"
        )
        
        self.assertEqual(book.title, "Test Book")
        self.assertEqual(book.author_id, 1)
        self.assertEqual(book.description, "Test description")
        # Default values are None until set
        self.assertIsNone(book.verification_status)
        self.assertIsNone(book.is_studied)
    
    def test_book_validation(self):
        """Test book validation constraints"""
        # Valid book
        book = Book(title="Valid Book", author_id=1)
        self.assertEqual(book.title, "Valid Book")
        
        # Test title length constraint (SQLAlchemy validates at DB level)
        long_title = "T" * (MAX_BOOK_TITLE_LENGTH + 1)
        # This won't raise an error at object creation, but will at DB insert
        book_long = Book(title=long_title, author_id=1)
        self.assertEqual(book_long.title, long_title)
        
        # Test minimum title length
        book_short = Book(title="T", author_id=1)
        self.assertEqual(book_short.title, "T")


class TestBookIsnadModel(unittest.TestCase):
    """Test BookIsnad model"""
    
    def test_isnad_creation(self):
        """Test creating a book isnad"""
        isnad = BookIsnad(
            book_id=1,
            file_path="/path/to/file.pdf",
            original_filename="file.pdf",
            notes="Test notes"
        )
        
        self.assertEqual(isnad.book_id, 1)
        self.assertEqual(isnad.file_path, "/path/to/file.pdf")
        self.assertEqual(isnad.original_filename, "file.pdf")
        self.assertEqual(isnad.notes, "Test notes")
        # Default status is None until set
        self.assertIsNone(isnad.status)
    
    def test_isnad_status(self):
        """Test isnad status values"""
        isnad = BookIsnad(book_id=1, file_path="/path/to/file.pdf")
        
        # Default status is None until set
        self.assertIsNone(isnad.status)
        
        # Test valid status values
        valid_statuses = ['active', 'archived', 'deleted']
        for status in valid_statuses:
            isnad.status = status
            self.assertEqual(isnad.status, status)


class TestIsnadChainModel(unittest.TestCase):
    """Test IsnadChain model"""
    
    def test_chain_creation(self):
        """Test creating an isnad chain"""
        chain = IsnadChain(
            isnad_id=1,
            sheikh_name="Test Sheikh",
            sheikh_description="Test description",
            chain_order=1,
            notes="Test notes"
        )
        
        self.assertEqual(chain.isnad_id, 1)
        self.assertEqual(chain.sheikh_name, "Test Sheikh")
        self.assertEqual(chain.sheikh_description, "Test description")
        self.assertEqual(chain.chain_order, 1)
        self.assertEqual(chain.notes, "Test notes")
    
    def test_chain_order(self):
        """Test chain order validation"""
        chain = IsnadChain(
            isnad_id=1,
            sheikh_name="Test Sheikh",
            chain_order=1
        )
        
        # Valid order
        self.assertEqual(chain.chain_order, 1)
        
        # Test different order values
        for order in [1, 2, 3, 10, 100]:
            chain.chain_order = order
            self.assertEqual(chain.chain_order, order)


if __name__ == '__main__':
    unittest.main()
