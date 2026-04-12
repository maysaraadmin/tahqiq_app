"""
Database constants for model constraints
"""
from config import config

# Year constraints
MIN_YEAR = 0
MAX_YEAR = 3000

# String length constraints
MAX_AUTHOR_NAME_LENGTH = 200
MAX_BOOK_TITLE_LENGTH = 300
MAX_LIBRARY_NAME_LENGTH = 200
MAX_SHELF_NUMBER_LENGTH = 100
MAX_COPYIST_LENGTH = 200

# Validation patterns
AUTHOR_NAME_PATTERN = r'^[^<>;&\x00-\x1f\x7f-\x9f]+$'
BOOK_TITLE_PATTERN = r'^[^<>;&\x00-\x1f\x7f-\x9f]{2,}$'
LIBRARY_NAME_PATTERN = r'^[^<>;&\x00-\x1f\x7f-\x9f]{2,}$|^$'
SHELF_NUMBER_PATTERN = r'^[A-Za-z0-9\-]*$|^$'
COPYIST_PATTERN = r'^[^<>;&\x00-\x1f\x7f-\x9f]{2,}$|^$'

# Relation types
VALID_RELATION_TYPES = ['سماع', 'إجازة', 'قراءة', 'تلمذ', 'إجازة خاصة']

# Verification statuses
VERIFICATION_STATUSES = ['not_started', 'in_progress', 'verified', 'completed']
