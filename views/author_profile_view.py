from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QTableWidget, QTableWidgetItem,
                             QTabWidget, QHeaderView, QMessageBox, QProgressBar,
                             QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt
from controllers.study_controller import StudyController
from controllers.relation_controller import RelationController

class AuthorProfileView(QWidget):
    def __init__(self, author_controller, author_data):
        super().__init__()
        self.author_controller = author_controller
        self.study_controller = StudyController()
        self.relation_controller = RelationController()
        self.author_data = author_data
        
        self.setup_ui()
        self.load_author_profile()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Author header
        self.setup_author_header(layout)
        
        # Tabs for different sections
        tabs = QTabWidget()
        tabs.addTab(self.setup_books_tab(), "Books & Study Progress")
        tabs.addTab(self.setup_relations_tab(), "Teachers & Students")
        tabs.addTab(self.setup_study_tab(), "Study Sessions")
        layout.addWidget(tabs)
    
    def setup_author_header(self, parent_layout):
        header_group = QGroupBox("Author Profile")
        header_layout = QGridLayout(header_group)
        
        # Basic info
        name_label = QLabel(f"<h2>{self.author_data['name']}</h2>")
        name_label.setStyleSheet("color: #2c3e50; font-weight: bold;")
        header_layout.addWidget(name_label, 0, 0, 1, 2)
        
        # Years
        years_text = f"Born: {self.author_data.get('birth_year', 'Unknown')}"
        if self.author_data.get('death_year'):
            years_text += f" - Died: {self.author_data['death_year']}"
        years_label = QLabel(years_text)
        header_layout.addWidget(years_label, 1, 0)
        
        # Bio
        if self.author_data.get('bio'):
            bio_label = QLabel(f"Bio: {self.author_data['bio']}")
            bio_label.setWordWrap(True)
            header_layout.addWidget(bio_label, 2, 0, 1, 2)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.load_author_profile)
        btn_layout.addWidget(self.refresh_btn)
        
        self.study_btn = QPushButton("Start Study Session")
        self.study_btn.clicked.connect(self.start_study_session)
        btn_layout.addWidget(self.study_btn)
        
        btn_layout.addStretch()
        header_layout.addLayout(btn_layout, 3, 0, 1, 2)
        
        parent_layout.addWidget(header_group)
    
    def setup_books_tab(self):
        books_widget = QWidget()
        layout = QVBoxLayout(books_widget)
        
        # Study progress overview
        progress_group = QGroupBox("Study Progress")
        progress_layout = QGridLayout(progress_group)
        
        self.total_books_label = QLabel("Total Books: 0")
        self.studied_books_label = QLabel("Studied: 0")
        self.verified_books_label = QLabel("Verified: 0")
        self.completed_books_label = QLabel("Completed: 0")
        
        progress_layout.addWidget(self.total_books_label, 0, 0)
        progress_layout.addWidget(self.studied_books_label, 0, 1)
        progress_layout.addWidget(self.verified_books_label, 1, 0)
        progress_layout.addWidget(self.completed_books_label, 1, 1)
        
        # Progress bars
        self.study_progress_bar = QProgressBar()
        self.study_progress_bar.setFormat("Study Progress: %p%")
        progress_layout.addWidget(self.study_progress_bar, 2, 0, 1, 2)
        
        self.verification_progress_bar = QProgressBar()
        self.verification_progress_bar.setFormat("Verification Progress: %p%")
        progress_layout.addWidget(self.verification_progress_bar, 3, 0, 1, 2)
        
        layout.addWidget(progress_group)
        
        # Books table
        books_label = QLabel("Books:")
        books_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        layout.addWidget(books_label)
        
        self.books_table = QTableWidget()
        self.books_table.setColumnCount(6)
        self.books_table.setHorizontalHeaderLabels([
            "Title", "Status", "Studied", "Sessions", "Verification Date", "Actions"
        ])
        self.books_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.books_table)
        
        return books_widget
    
    def setup_relations_tab(self):
        relations_widget = QWidget()
        layout = QVBoxLayout(relations_widget)
        
        # Teachers section
        teachers_group = QGroupBox("Teachers (Shuyukh)")
        teachers_layout = QVBoxLayout(teachers_group)
        
        self.teachers_table = QTableWidget()
        self.teachers_table.setColumnCount(3)
        self.teachers_table.setHorizontalHeaderLabels(["Name", "Relation Type", "Actions"])
        self.teachers_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        teachers_layout.addWidget(self.teachers_table)
        
        layout.addWidget(teachers_group)
        
        # Students section
        students_group = QGroupBox("Students")
        students_layout = QVBoxLayout(students_group)
        
        self.students_table = QTableWidget()
        self.students_table.setColumnCount(3)
        self.students_table.setHorizontalHeaderLabels(["Name", "Relation Type", "Actions"])
        self.students_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        students_layout.addWidget(self.students_table)
        
        layout.addWidget(students_group)
        
        return relations_widget
    
    def setup_study_tab(self):
        study_widget = QWidget()
        layout = QVBoxLayout(study_widget)
        
        # Study sessions table
        sessions_label = QLabel("Study Sessions:")
        sessions_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        layout.addWidget(sessions_label)
        
        self.sessions_table = QTableWidget()
        self.sessions_table.setColumnCount(5)
        self.sessions_table.setHorizontalHeaderLabels([
            "Date", "Duration", "Pages", "Key Findings", "Actions"
        ])
        self.sessions_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.sessions_table)
        
        # Add new session button
        add_session_btn = QPushButton("Add Study Session")
        add_session_btn.clicked.connect(self.add_study_session)
        layout.addWidget(add_session_btn)
        
        return study_widget
    
    def load_author_profile(self):
        try:
            # Load study summary
            summary = self.study_controller.get_author_study_summary(self.author_data['id'])
            
            # Update progress labels
            self.total_books_label.setText(f"Total Books: {summary['total_books']}")
            self.studied_books_label.setText(f"Studied: {summary['studied_books']}")
            self.verified_books_label.setText(f"Verified: {summary['verified_books']}")
            self.completed_books_label.setText(f"Completed: {summary['completed_books']}")
            
            # Update progress bars
            study_progress = (summary['studied_books'] / summary['total_books'] * 100) if summary['total_books'] > 0 else 0
            verification_progress = (summary['verified_books'] / summary['total_books'] * 100) if summary['total_books'] > 0 else 0
            
            self.study_progress_bar.setValue(int(study_progress))
            self.verification_progress_bar.setValue(int(verification_progress))
            
            # Load books table
            self.load_books_table(summary['books'])
            
            # Load relations
            self.load_relations()
            
            # Load study sessions
            self.load_study_sessions()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load author profile: {e}")
    
    def load_books_table(self, books):
        self.books_table.setRowCount(len(books))
        
        for row, book in enumerate(books):
            self.books_table.setItem(row, 0, QTableWidgetItem(book['title']))
            self.books_table.setItem(row, 1, QTableWidgetItem(book['verification_status'].replace('_', ' ').title()))
            self.books_table.setItem(row, 2, QTableWidgetItem("Yes" if book['is_studied'] else "No"))
            self.books_table.setItem(row, 3, QTableWidgetItem(str(book['study_sessions_count'])))
            
            date_str = book['verification_date'].strftime('%Y-%m-%d') if book['verification_date'] else "Not verified"
            self.books_table.setItem(row, 4, QTableWidgetItem(date_str))
            
            # Add action buttons
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(2, 2, 2, 2)
            
            study_btn = QPushButton("Study")
            study_btn.clicked.connect(lambda checked, book_id=book['id']: self.study_book(book_id))
            study_btn.setMaximumWidth(50)
            
            verify_btn = QPushButton("Verify")
            verify_btn.clicked.connect(lambda checked, book_id=book['id']: self.verify_book(book_id))
            verify_btn.setMaximumWidth(50)
            
            btn_layout.addWidget(study_btn)
            btn_layout.addWidget(verify_btn)
            btn_layout.addStretch()
            
            self.books_table.setCellWidget(row, 5, btn_widget)
    
    def load_relations(self):
        try:
            relations = self.relation_controller.get_author_relations(self.author_data['id'])
            
            # Separate teachers and students
            teachers = [rel for rel in relations if rel['type'] == 'sheikh']
            students = [rel for rel in relations if rel['type'] == 'student']
            
            # Load teachers table
            self.teachers_table.setRowCount(len(teachers))
            for row, teacher in enumerate(teachers):
                self.teachers_table.setItem(row, 0, QTableWidgetItem(teacher['name']))
                self.teachers_table.setItem(row, 1, QTableWidgetItem(teacher['relation_type'] or ''))
                self.teachers_table.setItem(row, 2, QTableWidgetItem("View Profile"))
            
            # Load students table
            self.students_table.setRowCount(len(students))
            for row, student in enumerate(students):
                self.students_table.setItem(row, 0, QTableWidgetItem(student['name']))
                self.students_table.setItem(row, 1, QTableWidgetItem(student['relation_type'] or ''))
                self.students_table.setItem(row, 2, QTableWidgetItem("View Profile"))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load relations: {e}")
    
    def load_study_sessions(self):
        # This would load all study sessions for this author's books
        # For now, show empty table
        self.sessions_table.setRowCount(0)
    
    def study_book(self, book_id):
        # Open study dialog for specific book
        QMessageBox.information(self, "Study", f"Study session for book ID: {book_id}")
    
    def verify_book(self, book_id):
        # Open verification dialog for specific book
        QMessageBox.information(self, "Verify", f"Verify book ID: {book_id}")
    
    def start_study_session(self):
        # Start study session for this author
        QMessageBox.information(self, "Study Session", "Starting study session for author")
    
    def add_study_session(self):
        # Add new study session
        QMessageBox.information(self, "Add Session", "Adding new study session")
