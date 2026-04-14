from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QFormLayout, QMessageBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QFileDialog, QGroupBox, QScrollArea, QComboBox,
                             QLineEdit, QWidget, QSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal
from controllers.book_controller import BookController
from controllers.author_controller import AuthorController
from controllers.isnad_controller import IsnadController
from config import config
import os
import re
import logging

logger = logging.getLogger(__name__)

class IsnadDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Book for Investigation")
        self.setMinimumWidth(1200)
        self.setMinimumHeight(900)
        self.resize(1200, 900)
        
        self.book_controller = BookController()
        self.author_controller = AuthorController()
        self.isnad_controller = IsnadController()
        
        self.current_book_id = None
        self.uploaded_file_path = None
        self.isnad_chain = []
        
        self.setup_ui()
        self.load_authors()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Book selection section
        book_group = QGroupBox("Step 1: Select Book")
        book_layout = QFormLayout(book_group)
        
        # Author selection
        self.author_combo = QComboBox()
        self.author_combo.currentIndexChanged.connect(self.on_author_changed)
        book_layout.addRow("Author:", self.author_combo)
        
        # Book selection or creation
        book_select_layout = QHBoxLayout()
        
        self.book_combo = QComboBox()
        self.book_combo.setEnabled(False)
        book_select_layout.addWidget(self.book_combo)
        
        self.new_book_btn = QPushButton("New Book")
        self.new_book_btn.clicked.connect(self.add_new_book)
        book_select_layout.addWidget(self.new_book_btn)
        
        book_layout.addRow("Book:", book_select_layout)
        
        # Book details
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Book title")
        book_layout.addRow("Title:", self.title_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        self.description_edit.setPlaceholderText("Book description (optional)")
        book_layout.addRow("Description:", self.description_edit)
        
        scroll_layout.addWidget(book_group)
        
        # File upload section
        file_group = QGroupBox("Step 2: Upload Book File")
        file_layout = QVBoxLayout(file_group)
        
        # Upload controls
        upload_controls = QHBoxLayout()
        
        self.upload_btn = QPushButton("Select File (PDF/Word)")
        self.upload_btn.clicked.connect(self.upload_book_file)
        upload_controls.addWidget(self.upload_btn)
        
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("QLabel { color: gray; }")
        upload_controls.addWidget(self.file_label)
        
        upload_controls.addStretch()
        file_layout.addLayout(upload_controls)
        
        scroll_layout.addWidget(file_group)
        
        # Isnad chain section
        isnad_group = QGroupBox("Step 3: Isnad Chain")
        isnad_layout = QVBoxLayout(isnad_group)
        
        # Instructions
        instructions = QLabel(
            "Enter the isnad chain from your sheikhs to the author. "
            "Start from the sheikh you received the book from and end with the author."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }")
        isnad_layout.addWidget(instructions)
        
        # Current isnad chain display
        self.isnad_display = QTextEdit()
        self.isnad_display.setMaximumHeight(150)
        self.isnad_display.setReadOnly(True)
        self.isnad_display.setPlaceholderText("Isnad chain will appear here...")
        isnad_layout.addWidget(QLabel("Current Isnad:"))
        isnad_layout.addWidget(self.isnad_display)
        
        # Add sheikh form
        add_sheikh_layout = QFormLayout()
        
        self.sheikh_name_edit = QLineEdit()
        self.sheikh_name_edit.setPlaceholderText("Sheikh name")
        add_sheikh_layout.addRow("Sheikh Name:", self.sheikh_name_edit)
        
        self.sheikh_description_edit = QTextEdit()
        self.sheikh_description_edit.setMaximumHeight(60)
        self.sheikh_description_edit.setPlaceholderText("Sheikh description or notes (optional)")
        add_sheikh_layout.addRow("Description:", self.sheikh_description_edit)
        
        self.sheikh_order_spin = QSpinBox()
        self.sheikh_order_spin.setMinimum(1)
        self.sheikh_order_spin.setMaximum(100)
        self.sheikh_order_spin.setValue(len(self.isnad_chain) + 1)
        add_sheikh_layout.addRow("Order:", self.sheikh_order_spin)
        
        isnad_layout.addLayout(add_sheikh_layout)
        
        # Add/Remove buttons
        isnad_buttons = QHBoxLayout()
        
        self.add_sheikh_btn = QPushButton("Add Sheikh to Isnad")
        self.add_sheikh_btn.clicked.connect(self.add_sheikh_to_isnad)
        isnad_buttons.addWidget(self.add_sheikh_btn)
        
        self.remove_sheikh_btn = QPushButton("Remove Last Sheikh")
        self.remove_sheikh_btn.clicked.connect(self.remove_last_sheikh)
        isnad_buttons.addWidget(self.remove_sheikh_btn)
        
        self.clear_isnad_btn = QPushButton("Clear Isnad")
        self.clear_isnad_btn.clicked.connect(self.clear_isnad)
        isnad_buttons.addWidget(self.clear_isnad_btn)
        
        isnad_buttons.addStretch()
        isnad_layout.addLayout(isnad_buttons)
        
        scroll_layout.addWidget(isnad_group)
        
        # Isnad table
        table_group = QGroupBox("Isnad Details")
        table_layout = QVBoxLayout(table_group)
        
        self.isnad_table = QTableWidget()
        self.isnad_table.setColumnCount(5)
        self.isnad_table.setHorizontalHeaderLabels(["Order", "Sheikh Name", "Description", "Date", "Actions"])
        self.isnad_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table_layout.addWidget(self.isnad_table)
        
        scroll_layout.addWidget(table_group)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save Isnad")
        self.save_btn.clicked.connect(self.save_isnad)
        self.save_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 15px; font-size: 14px; font-weight: bold; min-width: 120px; }")
        self.save_btn.setEnabled(False)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; padding: 15px; font-size: 14px; min-width: 100px; }")
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.save_btn)
        
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
            
            for author in sorted(authors, key=lambda x: x['name']):
                self.author_combo.addItem(author['name'], author['id'])
                
        except Exception as e:
            logger.error(f"Failed to load authors: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load authors: {e}")

    def on_author_changed(self):
        """Handle author selection change"""
        author_id = self.author_combo.currentData()
        
        if not author_id:
            if hasattr(self.book_combo, 'clear'):
                self.book_combo.clear()
            if hasattr(self.book_combo, 'setEnabled'):
                self.book_combo.setEnabled(False)
            return
        
        try:
            books = self.book_controller.get_author_books(author_id)
            
            if hasattr(self.book_combo, 'clear'):
                self.book_combo.clear()
            
            if not books:
                if hasattr(self.book_combo, 'addItem'):
                    self.book_combo.addItem("No books available for this author", None)
                if hasattr(self.book_combo, 'setEnabled'):
                    self.book_combo.setEnabled(False)
                return
            
            if hasattr(self.book_combo, 'addItem'):
                self.book_combo.addItem("Select book...", None)
            for book in sorted(books, key=lambda x: x['title']):
                if hasattr(self.book_combo, 'addItem'):
                    self.book_combo.addItem(book['title'], book['id'])
            
            if hasattr(self.book_combo, 'setEnabled'):
                self.book_combo.setEnabled(True)
                # Connect signal only once
                if not hasattr(self, '_book_signal_connected'):
                    self.book_combo.currentIndexChanged.connect(self.check_save_conditions)
                    self._book_signal_connected = True
                self.check_save_conditions()
            
        except Exception as e:
            logger.error(f"Failed to load books: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load books: {e}")

    def add_new_book(self):
        """Add new book dialog"""
        from views.book_dialog import BookDialog
        
        # Get authors for the dialog
        authors = self.author_controller.get_all_authors()
        
        dialog = BookDialog(authors, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Reload authors and books
            self.load_authors()
            # Select newly added author
            if hasattr(dialog, 'new_author_id'):
                for i in range(self.author_combo.count()):
                    if self.author_combo.itemData(i) == dialog.new_author_id:
                        self.author_combo.setCurrentIndex(i)
                        break

    def upload_book_file(self):
        """Upload book file with security validation"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Book File",
            "",
            "PDF Files (*.pdf);;Word Documents (*.docx *.doc);;Text Files (*.txt);;All Files (*)"
        )
        
        if not file_path:
            return
        
        try:
            # Security: Validate file path
            if not os.path.exists(file_path):
                QMessageBox.warning(self, "Error", "File does not exist")
                return
            
            # Security: Check file size
            file_size = os.path.getsize(file_path)
            max_size = config.MAX_FILE_SIZE_BYTES
            if file_size > max_size:
                QMessageBox.warning(self, "Error", f"File too large. Maximum size is {config.MAX_FILE_SIZE_MB}MB")
                return
            
            # Security: Validate file extension
            allowed_extensions = ['.pdf', '.docx', '.doc', '.txt']
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in allowed_extensions:
                QMessageBox.warning(self, "Error", f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}")
                return
            
            # Security: Sanitize filename
            filename = os.path.basename(file_path)
            # Remove dangerous characters
            safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            if safe_filename != filename:
                logger.warning(f"Sanitized filename from {filename} to {safe_filename}")
            
            # Store the file path
            self.uploaded_file_path = file_path
            
            # Update UI
            self.file_label.setText(f"File: {safe_filename}")
            self.file_label.setStyleSheet("QLabel { color: green; }")
            
            # If title is empty, use sanitized filename
            if not self.title_edit.text().strip():
                title = os.path.splitext(safe_filename)[0]
                # Clean title for display
                title = re.sub(r'[_\-.]+', ' ', title).strip()
                self.title_edit.setText(title)
            
            logger.info(f"Selected book file: {safe_filename} ({file_size} bytes)")
            self.check_save_conditions()
            
        except Exception as e:
            logger.error(f"Failed to select file: {e}")
            QMessageBox.critical(self, "Error", f"Failed to select file: {e}")

    def add_sheikh_to_isnad(self):
        """Add sheikh to isnad chain"""
        sheikh_name = self.sheikh_name_edit.text().strip()
        if not sheikh_name:
            QMessageBox.warning(self, "Warning", "Please enter sheikh name")
            return
        
        sheikh_data = {
            'name': sheikh_name,
            'description': self.sheikh_description_edit.toPlainText().strip(),
            'order': self.sheikh_order_spin.value()
        }
        
        self.isnad_chain.append(sheikh_data)
        self.update_isnad_display()
        self.update_isnad_table()
        
        # Clear form
        self.sheikh_name_edit.clear()
        self.sheikh_description_edit.clear()
        self.sheikh_order_spin.setValue(len(self.isnad_chain) + 1)
        
        # Enable save button if we have data
        self.check_save_conditions()

    def remove_last_sheikh(self):
        """Remove last sheikh from isnad"""
        if self.isnad_chain:
            self.isnad_chain.pop()
            self.update_isnad_display()
            self.update_isnad_table()
            self.sheikh_order_spin.setValue(len(self.isnad_chain) + 1)
            self.check_save_conditions()

    def clear_isnad(self):
        """Clear entire isnad chain"""
        reply = QMessageBox.question(self, "Confirm", "Do you want to clear the entire isnad?")
        if reply == QMessageBox.StandardButton.Yes:
            self.isnad_chain.clear()
            self.update_isnad_display()
            self.update_isnad_table()
            self.sheikh_order_spin.setValue(1)
            self.check_save_conditions()

    def update_isnad_display(self):
        """Update the isnad display"""
        if not self.isnad_chain:
            self.isnad_display.clear()
            return
        
        # Sort by order
        sorted_chain = sorted(self.isnad_chain, key=lambda x: x['order'])
        
        isnad_text = "Isnad Chain:\n"
        for i, sheikh in enumerate(sorted_chain):
            isnad_text += f"{i+1}. {sheikh['name']}"
            if sheikh['description']:
                isnad_text += f" - {sheikh['description']}"
            isnad_text += "\n"
        
        self.isnad_display.setPlainText(isnad_text)

    def update_isnad_table(self):
        """Update the isnad table"""
        self.isnad_table.setRowCount(len(self.isnad_chain))
        
        # Sort by order
        sorted_chain = sorted(self.isnad_chain, key=lambda x: x['order'])
        
        for i, sheikh in enumerate(sorted_chain):
            self.isnad_table.setItem(i, 0, QTableWidgetItem(str(sheikh['order'])))
            self.isnad_table.setItem(i, 1, QTableWidgetItem(sheikh['name']))
            self.isnad_table.setItem(i, 2, QTableWidgetItem(sheikh['description'] or ''))
            self.isnad_table.setItem(i, 3, QTableWidgetItem(""))
            
            # Add remove button
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda checked, idx=i: self.remove_sheikh_at_index(idx))
            self.isnad_table.setCellWidget(i, 4, remove_btn)

    def remove_sheikh_at_index(self, index):
        """Remove sheikh at specific index"""
        if 0 <= index < len(self.isnad_chain):
            sheikh_name = self.isnad_chain[index]['name']
            reply = QMessageBox.question(self, "Confirm", f"Do you want to remove {sheikh_name} from the isnad?")
            if reply == QMessageBox.StandardButton.Yes:
                self.isnad_chain.pop(index)
                # Reorder remaining
                for i, sheikh in enumerate(self.isnad_chain):
                    sheikh['order'] = i + 1
                self.update_isnad_display()
                self.update_isnad_table()
                self.sheikh_order_spin.setValue(len(self.isnad_chain) + 1)
                self.check_save_conditions()

    def check_save_conditions(self):
        """Check if save button should be enabled"""
        # Check if we have a selected book OR new book data with file
        has_selected_book = False
        if hasattr(self.book_combo, 'currentData'):
            has_selected_book = self.book_combo.currentData() is not None
        
        has_new_book = self.title_edit.text().strip() and self.uploaded_file_path
        has_book = has_selected_book or has_new_book
        has_isnad = len(self.isnad_chain) > 0
        
        self.save_btn.setEnabled(bool(has_book and has_isnad))
        
        # Debug info (only in development)
        if config.LOG_LEVEL == 'DEBUG':
            logger.info(f"Save button check - has_book: {has_book}, has_isnad: {has_isnad}")
            logger.info(f"Selected book: {has_selected_book}, New book: {has_new_book}")
            logger.info(f"Chain length: {len(self.isnad_chain)}")

    def save_isnad(self):
        """Save isnad"""
        try:
            # Validate data
            if not self.title_edit.text().strip():
                QMessageBox.warning(self, "Warning", "Please enter book title")
                return
            
            if not self.uploaded_file_path:
                QMessageBox.warning(self, "Warning", "Please upload book file")
                return
            
            if not self.isnad_chain:
                QMessageBox.warning(self, "Warning", "Please add isnad chain")
                return
            
            # Get or create book
            book_id = None
            if hasattr(self.book_combo, 'currentData'):
                book_id = self.book_combo.currentData()
            if not book_id:
                # Create new book
                author_id = self.author_combo.currentData()
                book_id = self.book_controller.add_book(
                    title=self.title_edit.text().strip(),
                    author_id=author_id,
                    description=self.description_edit.toPlainText().strip()
                )
            
            # Save isnad
            isnad_id = self.isnad_controller.create_isnad(
                book_id=book_id,
                file_path=self.uploaded_file_path,
                isnad_chain=self.isnad_chain
            )
            
            QMessageBox.information(self, "Success", f"Isnad saved successfully (ID: {isnad_id})")
            self.accept()
            
        except Exception as e:
            logger.error(f"Failed to save isnad: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save isnad: {e}")

    def get_isnad_data(self):
        """Get the saved isnad data"""
        return getattr(self, 'saved_isnad_data', None)
