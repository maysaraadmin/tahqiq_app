from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QTextEdit, QFormLayout,
                             QMessageBox, QGroupBox, QScrollArea, QWidget)
from PyQt6.QtCore import Qt
from controllers.author_controller import AuthorController
from controllers.book_controller import BookController
import logging

logger = logging.getLogger(__name__)

class BookSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Book for Investigation")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self.author_controller = AuthorController()
        self.book_controller = BookController()
        
        self.setup_ui()
        self.load_authors()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create scroll area for content
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Instructions
        instructions = QLabel(
            "Select a book to start a new investigation. "
            "You will be able to upload manuscript files and compare different versions."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }")
        scroll_layout.addWidget(instructions)
        
        # Author selection
        author_group = QGroupBox("Step 1: Select Author")
        author_layout = QFormLayout(author_group)
        
        self.author_combo = QComboBox()
        self.author_combo.currentIndexChanged.connect(self.on_author_changed)
        author_layout.addRow("Author:", self.author_combo)
        
        scroll_layout.addWidget(author_group)
        
        # Book selection
        book_group = QGroupBox("Step 2: Select Book")
        book_layout = QFormLayout(book_group)
        
        self.book_combo = QComboBox()
        self.book_combo.setEnabled(False)
        book_layout.addRow("Book:", self.book_combo)
        
        scroll_layout.addWidget(book_group)
        
        # Investigation details
        details_group = QGroupBox("Step 3: Investigation Details")
        details_layout = QFormLayout(details_group)
        
        self.title_edit = QTextEdit()
        self.title_edit.setMaximumHeight(60)
        self.title_edit.setPlaceholderText("Enter investigation title (optional)")
        details_layout.addRow("Investigation Title:", self.title_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Describe the investigation objectives and scope...")
        details_layout.addRow("Description:", self.description_edit)
        
        self.methodology_edit = QTextEdit()
        self.methodology_edit.setMaximumHeight(80)
        self.methodology_edit.setPlaceholderText("Describe your research methodology...")
        details_layout.addRow("Methodology:", self.methodology_edit)
        
        self.objectives_edit = QTextEdit()
        self.objectives_edit.setMaximumHeight(80)
        self.objectives_edit.setPlaceholderText("List your research objectives...")
        details_layout.addRow("Objectives:", self.objectives_edit)
        
        scroll_layout.addWidget(details_group)
        
        # Book info display
        self.info_group = QGroupBox("Book Information")
        info_layout = QVBoxLayout(self.info_group)
        
        self.book_info_label = QLabel("Select a book to view information")
        self.book_info_label.setWordWrap(True)
        info_layout.addWidget(self.book_info_label)
        
        scroll_layout.addWidget(self.info_group)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Investigation")
        self.start_btn.clicked.connect(self.start_investigation)
        self.start_btn.setEnabled(False)
        self.start_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 10px; }")
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.start_btn)
        
        layout.addLayout(button_layout)

    def load_authors(self):
        """Load authors into combo box"""
        try:
            authors = self.author_controller.get_all_authors()
            
            self.author_combo.clear()
            
            if not authors:
                self.author_combo.addItem("No authors available", None)
                self.author_combo.setEnabled(False)
                return
            
            # Add authors sorted by name
            for author in sorted(authors, key=lambda x: x['name']):
                self.author_combo.addItem(author['name'], author['id'])
                
        except Exception as e:
            logger.error(f"Failed to load authors: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load authors: {e}")

    def on_author_changed(self):
        """Handle author selection change"""
        author_id = self.author_combo.currentData()
        
        if not author_id:
            self.book_combo.clear()
            self.book_combo.setEnabled(False)
            self.book_info_label.setText("Select a book to view information")
            self.start_btn.setEnabled(False)
            return
        
        try:
            # Load books for selected author
            books = self.book_controller.get_author_books(author_id)
            
            self.book_combo.clear()
            
            if not books:
                self.book_combo.addItem("No books available for this author", None)
                self.book_combo.setEnabled(False)
                self.book_info_label.setText("This author has no books in the system")
                self.start_btn.setEnabled(False)
                return
            
            # Add books sorted by title
            for book in sorted(books, key=lambda x: x['title']):
                self.book_combo.addItem(book['title'], book['id'])
            
            self.book_combo.setEnabled(True)
            self.on_book_changed()  # Update info for first book
            
        except Exception as e:
            logger.error(f"Failed to load books: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load books: {e}")

    def on_book_changed(self):
        """Handle book selection change"""
        book_id = self.book_combo.currentData()
        
        if not book_id:
            self.book_info_label.setText("Select a book to view information")
            self.start_btn.setEnabled(False)
            return
        
        try:
            # Get book details
            books = self.book_controller.get_author_books(self.author_combo.currentData())
            selected_book = None
            
            for book in books:
                if book['id'] == book_id:
                    selected_book = book
                    break
            
            if not selected_book:
                self.book_info_label.setText("Book information not available")
                self.start_btn.setEnabled(False)
                return
            
            # Get manuscript count
            from controllers.manuscript_controller import ManuscriptController
            manuscript_controller = ManuscriptController()
            manuscripts = manuscript_controller.get_book_manuscripts(book_id)
            
            # Display book information
            info_text = f"<b>Book:</b> {selected_book['title']}<br>"
            info_text += f"<b>Author:</b> {selected_book['author_name']}<br>"
            info_text += f"<b>Status:</b> {selected_book.get('verification_status', 'Unknown')}<br>"
            info_text += f"<b>Manuscripts:</b> {len(manuscripts)} available<br>"
            
            if selected_book.get('description'):
                info_text += f"<b>Description:</b> {selected_book['description']}<br>"
            
            if manuscripts:
                info_text += "<br><b>Available Manuscripts:</b><br>"
                for ms in manuscripts[:5]:  # Show first 5 manuscripts
                    info_text += f"  - {ms['library_name']}, Shelf: {ms['shelf_number']}<br>"
                if len(manuscripts) > 5:
                    info_text += f"  ... and {len(manuscripts) - 5} more<br>"
            
            self.book_info_label.setText(info_text)
            self.start_btn.setEnabled(True)
            
        except Exception as e:
            logger.error(f"Failed to load book info: {e}")
            self.book_info_label.setText("Failed to load book information")
            self.start_btn.setEnabled(False)

    def start_investigation(self):
        """Start new investigation"""
        book_id = self.book_combo.currentData()
        if not book_id:
            QMessageBox.warning(self, "Warning", "Please select a book")
            return
        
        # Get investigation details
        title = self.title_edit.toPlainText().strip()
        description = self.description_edit.toPlainText().strip()
        methodology = self.methodology_edit.toPlainText().strip()
        objectives = self.objectives_edit.toPlainText().strip()
        
        # Validate at least title or description
        if not title and not description:
            QMessageBox.warning(self, "Warning", "Please provide at least a title or description for the investigation")
            return
        
        # Store data for parent to use
        self.investigation_data = {
            'book_id': book_id,
            'title': title,
            'description': description,
            'methodology': methodology,
            'objectives': objectives,
            'book_title': self.book_combo.currentText(),
            'author_name': self.author_combo.currentText()
        }
        
        self.accept()

    def get_investigation_data(self):
        """Get investigation data"""
        return getattr(self, 'investigation_data', None)
