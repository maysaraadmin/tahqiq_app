from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QTabWidget, QHeaderView, QSpinBox,
                             QLabel, QLineEdit, QMenuBar, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal
from datetime import datetime
from views.author_dialog import AuthorDialog
from views.book_dialog import BookDialog
from views.relations_widget import RelationsWidget
from controllers.author_controller import AuthorController
from controllers.book_controller import BookController
from controllers.manuscript_controller import ManuscriptController
import logging

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    # Custom signal for popup messages
    popup_signal = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.author_controller = AuthorController()
        self.book_controller = BookController()
        self.manuscript_controller = ManuscriptController()
        
        # Pagination state
        self.current_author_page = 0
        self.page_size = 50
        
        self.setup_ui()
        self.setup_menu()
        self.load_authors_table()
        
        # Connect popup signal to show messages
        self.popup_signal.connect(self.show_popup)

    def setup_ui(self):
        self.setWindowTitle("Tahqiq App - Authors and Books Management")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create tabs
        tabs = QTabWidget()
        tabs.addTab(self.setup_author_tab(), "Authors")
        tabs.addTab(self.setup_book_tab(), "Books")
        tabs.addTab(self.setup_manuscript_tab(), "Manuscripts")
        self.relations_widget = self.setup_relations_tab()
        tabs.addTab(self.relations_widget, "Relations")
        layout.addWidget(tabs)

    def setup_author_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Author")
        add_btn.clicked.connect(self.add_author)
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_author)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_authors)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(refresh_btn)
        export_btn = QPushButton("Export")
        # export_btn.clicked.connect(self.export_authors)
        export_btn.setStyleSheet("QPushButton { background-color: #27ae60; }")
        btn_layout.addWidget(export_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.author_search = QLineEdit()
        self.author_search.setPlaceholderText("Search authors...")
        # self.author_search.textChanged.connect(self.filter_authors)
        self.author_search.setAlignment(Qt.AlignmentFlag.AlignRight)
        search_layout.addWidget(self.author_search)
        search_layout.addStretch()
        layout.addLayout(search_layout)

        # Authors table
        self.author_table = QTableWidget()
        self.author_table.setColumnCount(5)
        self.author_table.setHorizontalHeaderLabels(["ID", "Name", "Birth Year", "Death Year", "Actions"])
        self.author_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.author_table.setSortingEnabled(True)
        layout.addWidget(self.author_table)
        
        # Pagination controls
        pagination_layout = QHBoxLayout()
        
        # Previous button
        self.prev_author_btn = QPushButton("Previous")
        self.prev_author_btn.clicked.connect(self.prev_author_page)
        self.prev_author_btn.setEnabled(False)
        pagination_layout.addWidget(self.prev_author_btn)
        
        # Page label
        self.author_page_label = QLabel("Page 1 of 1")
        pagination_layout.addWidget(self.author_page_label)
        
        # Next button
        self.next_author_btn = QPushButton("Next")
        self.next_author_btn.clicked.connect(self.next_author_page)
        self.next_author_btn.setEnabled(False)
        pagination_layout.addWidget(self.next_author_btn)
        
        # Page size selector
        pagination_layout.addWidget(QLabel("Page size:"))
        self.page_size_spin = QSpinBox()
        self.page_size_spin.setRange(10, 100)
        self.page_size_spin.setValue(50)
        self.page_size_spin.setSingleStep(10)
        self.page_size_spin.valueChanged.connect(self.change_author_page_size)
        pagination_layout.addWidget(self.page_size_spin)
        
        pagination_layout.addStretch()
        layout.addLayout(pagination_layout)
        
        return tab

    def setup_book_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Book")
        add_btn.clicked.connect(self.add_book)
        btn_layout.addWidget(add_btn)
        export_btn = QPushButton("Export")
        # export_btn.clicked.connect(self.export_books)
        export_btn.setStyleSheet("QPushButton { background-color: #27ae60; }")
        btn_layout.addWidget(export_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.book_search = QLineEdit()
        self.book_search.setPlaceholderText("Search books...")
        self.book_search.textChanged.connect(self.filter_books)
        self.book_search.setAlignment(Qt.AlignmentFlag.AlignRight)
        search_layout.addWidget(self.book_search)
        search_layout.addStretch()
        layout.addLayout(search_layout)

        self.book_table = QTableWidget()
        self.book_table.setColumnCount(6)
        self.book_table.setHorizontalHeaderLabels(["ID", "Title", "Author", "Status", "Studied", "Actions"])
        self.book_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.book_table.setSortingEnabled(True)
        layout.addWidget(self.book_table)
        self.load_books_table()
        
        return tab

    def setup_manuscript_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Manuscript")
        add_btn.clicked.connect(self.add_manuscript)
        btn_layout.addWidget(add_btn)
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.export_manuscripts)
        export_btn.setStyleSheet("QPushButton { background-color: #27ae60; }")
        btn_layout.addWidget(export_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.manuscript_search = QLineEdit()
        self.manuscript_search.setPlaceholderText("Search manuscripts...")
        self.manuscript_search.textChanged.connect(self.filter_manuscripts)
        self.manuscript_search.setAlignment(Qt.AlignmentFlag.AlignRight)
        search_layout.addWidget(self.manuscript_search)
        search_layout.addStretch()
        layout.addLayout(search_layout)

        self.manuscript_table = QTableWidget()
        self.manuscript_table.setColumnCount(6)
        self.manuscript_table.setHorizontalHeaderLabels([
            "ID", "Book", "Library", "Shelf", "Copyist", "Actions"
        ])
        self.manuscript_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.manuscript_table.setSortingEnabled(True)
        layout.addWidget(self.manuscript_table)
        self.load_manuscripts_table()
        
        return tab

    def setup_relations_tab(self):
        relations_widget = RelationsWidget(self.author_controller)
        return relations_widget

    def setup_menu(self):
        """Setup application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # Backup actions
        backup_action = file_menu.addAction("Create Backup")
        backup_action.triggered.connect(self.create_backup)
        
        restore_action = file_menu.addAction("Restore Backup")
        restore_action.triggered.connect(self.restore_backup)
        
        file_menu.addSeparator()
        
        # Export actions
        export_authors_action = file_menu.addAction("Export Authors")
        # export_authors_action.triggered.connect(self.export_authors)
        
        export_books_action = file_menu.addAction("Export Books")
        # export_books_action.triggered.connect(self.export_books)
        
        export_manuscripts_action = file_menu.addAction("Export Manuscripts")
        # export_manuscripts_action.triggered.connect(self.export_manuscripts)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about)

    def create_backup(self):
        """Create database backup"""
        from utils.backup_manager import BackupManager
        BackupManager.create_backup(self)

    def restore_backup(self):
        """Restore database from backup"""
        from utils.backup_manager import BackupManager
        if BackupManager.restore_backup(self):
            # Refresh all tables after restore
            self.load_authors_table()
            self.load_books_table()
            self.load_manuscripts_table()
            self.update_relations_widget()

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About Tahqiq App", 
                         "Tahqiq & Asanid Tracker v1.0\n\n"
                         "A comprehensive tool for managing Islamic manuscripts, "
                         "books, authors, and chains of transmission.\n\n"
                         "Features:\n"
                         " Author, Book, and Manuscript management\n"
                         " Sheikh-Student relationship tracking\n"
                         " Study session management\n"
                         " CSV export functionality\n"
                         " Database backup and restore\n"
                         " Arabic RTL support")

    def load_authors_table(self):
        try:
            offset = self.current_author_page * self.page_size
            authors = self.author_controller.get_all_authors(limit=self.page_size, offset=offset)
            
            self.author_table.setRowCount(len(authors))
            for row, author in enumerate(authors):
                self.author_table.setItem(row, 0, QTableWidgetItem(str(author['id'])))
                self.author_table.setItem(row, 1, QTableWidgetItem(author['name']))
                self.author_table.setItem(row, 2, QTableWidgetItem(str(author['birth_year'] or '')))
                self.author_table.setItem(row, 3, QTableWidgetItem(str(author['death_year'] or '')))
                
                # Add Edit, Delete, and Profile buttons
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(2, 2, 2, 2)
                
                profile_btn = QPushButton("Profile")
                profile_btn.clicked.connect(lambda checked, r=row: self.view_author_profile(r))
                profile_btn.setMaximumWidth(60)
                profile_btn.setStyleSheet("QPushButton { background-color: #3498db; }")
                
                edit_btn = QPushButton("Edit")
                edit_btn.clicked.connect(lambda checked, r=row: self.edit_author(r))
                edit_btn.setMaximumWidth(50)
                
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(lambda checked, r=row: self.delete_author(r))
                delete_btn.setMaximumWidth(50)
                delete_btn.setStyleSheet("QPushButton { background-color: #ff4444; }")
                
                btn_layout.addWidget(profile_btn)
                btn_layout.addWidget(edit_btn)
                btn_layout.addWidget(delete_btn)
                btn_layout.addStretch()
                
                self.author_table.setCellWidget(row, 4, btn_widget)
            
            # Update pagination controls
            self.update_author_pagination()
        except Exception as e:
            logger.error(f"Failed to load authors: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load authors: {e}")

    def update_author_pagination(self):
        """Update author pagination controls"""
        try:
            total_count = self.author_controller.get_author_count()
            total_pages = (total_count + self.page_size - 1) // self.page_size
            current_page_num = self.current_author_page + 1
            
            self.author_page_label.setText(f"Page {current_page_num} of {total_pages}")
            
            # Enable/disable buttons
            self.prev_author_btn.setEnabled(self.current_author_page > 0)
            self.next_author_btn.setEnabled(self.current_author_page < total_pages - 1)
        except Exception as e:
            self.author_page_label.setText("Error loading pages")

    def prev_author_page(self):
        """Go to previous author page"""
        if self.current_author_page > 0:
            self.current_author_page -= 1
            self.load_authors_table()

    def next_author_page(self):
        """Go to next author page"""
        self.current_author_page += 1
        self.load_authors_table()

    def change_author_page_size(self, size):
        """Change author page size"""
        self.page_size = size
        self.current_author_page = 0  # Reset to first page
        self.load_authors_table()

    def refresh_authors(self):
        """Refresh author table"""
        self.current_author_page = 0
        self.load_authors_table()
        self.update_relations_widget()  # Update relations widget

    def add_author(self):
        dialog = AuthorDialog(self)
        if dialog.exec():
            name = dialog.name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "Warning", "Name is required")
                return
            
            birth = dialog.birth_edit.text().strip()
            death = dialog.death_edit.text().strip()
            bio = dialog.bio_edit.toPlainText().strip()
            
            try:
                self.author_controller.add_author(
                    name,
                    birth if birth else None,
                    death if death else None,
                    bio
                )
                self.current_author_page = 0  # Reset to first page
                self.load_authors_table()
                self.update_relations_widget()  # Update relations widget
                self.popup_signal.emit(f"Author '{name}' added successfully")
            except ValueError as e:
                QMessageBox.warning(self, "Warning", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Add failed: {e}")

    def edit_author(self, row):
        """Edit an author"""
        try:
            # Get author data
            id_item = self.author_table.item(row, 0)
            if not id_item:
                QMessageBox.warning(self, "Error", "Author ID not found")
                return
            
            author_id = int(id_item.text())
            
            # Get full author data
            authors = self.author_controller.get_all_authors()
            author_data = None
            for author in authors:
                if author['id'] == author_id:
                    author_data = author
                    break
            
            if not author_data:
                QMessageBox.warning(self, "Error", "Author not found")
                return
            
            # Open edit dialog
            from views.author_edit_dialog import AuthorEditDialog
            dialog = AuthorEditDialog(author_data, self)
            if dialog.exec():
                data = dialog.get_data()
                self.author_controller.update_author(author_id, **data)
                self.load_authors_table()
                self.update_relations_widget()  # Update relations widget
                self.popup_signal.emit("Author updated successfully")
        
        except ValueError as e:
            QMessageBox.warning(self, "Warning", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Update failed: {e}")

    def delete_author(self, row=None):
        """Delete an author"""
        if row is None:
            row = self.author_table.currentRow()
        
        if row < 0:
            QMessageBox.warning(self, "Warning", "Please select an author to delete")
            return
        
        # Safe null reference check
        id_item = self.author_table.item(row, 0)
        if not id_item:
            QMessageBox.warning(self, "Error", "Author ID not found")
            return
        
        author_id = int(id_item.text())
        
        # Get author name for confirmation
        name_item = self.author_table.item(row, 1)
        author_name = name_item.text() if name_item else "Unknown author"
        
        # First try to delete without cascade
        try:
            self.author_controller.delete_author(author_id, cascade_delete=False)
            # If successful, refresh tables
            self.load_authors_table()
            self.update_relations_widget()
            self.popup_signal.emit(f"Author '{author_name}' deleted successfully")
        except ValueError as e:
            # If there are dependencies, show cascade delete warning
            if "linked to:" in str(e):
                reply = QMessageBox.question(
                    self,
                    "Cascade Delete Required",
                    f"{str(e)}\n\nDo you want to delete all linked data (books and relations)?\n\nThis action cannot be undone.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        self.author_controller.delete_author(author_id, cascade_delete=True)
                        self.load_authors_table()
                        self.load_books_table()  # Refresh books table too
                        self.update_relations_widget()
                        self.popup_signal.emit(f"Author '{author_name}' and all linked data deleted successfully")
                    except Exception as cascade_error:
                        QMessageBox.critical(self, "Error", f"Cascade delete failed: {cascade_error}")
            else:
                # Other validation error
                QMessageBox.warning(self, "Warning", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Delete failed: {e}")

    def update_author_pagination(self):
        """Update author pagination controls"""
        try:
            total_count = self.author_controller.get_author_count()
            total_pages = (total_count + self.page_size - 1) // self.page_size
            current_page_num = self.current_author_page + 1
            
            self.author_page_label.setText(f"Page {current_page_num} of {total_pages}")
            
            # Enable/disable buttons
            self.prev_author_btn.setEnabled(self.current_author_page > 0)
            self.next_author_btn.setEnabled(self.current_author_page < total_pages - 1)
        except Exception as e:
            self.author_page_label.setText("Error loading pages")

    def prev_author_page(self):
        """Go to previous author page"""
        if self.current_author_page > 0:
            self.current_author_page -= 1
            self.load_authors_table()

    def next_author_page(self):
        """Go to next author page"""
        self.current_author_page += 1
        self.load_authors_table()

    def change_author_page_size(self, size):
        """Change author page size"""
        self.page_size = size
        self.current_author_page = 0  # Reset to first page
        self.load_authors_table()

    
    def load_books_table(self):
        try:
            books = self.book_controller.get_all_books()
            self.book_table.setRowCount(len(books))
            for row, book in enumerate(books):
                self.book_table.setItem(row, 0, QTableWidgetItem(str(book['id'])))
                self.book_table.setItem(row, 1, QTableWidgetItem(book['title']))
                self.book_table.setItem(row, 2, QTableWidgetItem(book['author_name']))
                
                # Verification status
                status = book.get('verification_status', 'not_started')
                status_text = status.replace('_', ' ').title()
                self.book_table.setItem(row, 3, QTableWidgetItem(status_text))
                
                # Studied status
                studied_text = "Yes" if book.get('is_studied', False) else "No"
                self.book_table.setItem(row, 4, QTableWidgetItem(studied_text))
                
                # Add action buttons
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(2, 2, 2, 2)
                
                study_btn = QPushButton("Study")
                study_btn.clicked.connect(lambda checked, r=row: self.study_book(r))
                study_btn.setMaximumWidth(50)
                study_btn.setStyleSheet("QPushButton { background-color: #27ae60; }")
                
                verify_btn = QPushButton("Verify")
                verify_btn.clicked.connect(lambda checked, r=row: self.verify_book(r))
                verify_btn.setMaximumWidth(50)
                verify_btn.setStyleSheet("QPushButton { background-color: #f39c12; }")
                
                edit_btn = QPushButton("Edit")
                edit_btn.clicked.connect(lambda checked, r=row: self.edit_book(r))
                edit_btn.setMaximumWidth(50)
                
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(lambda checked, r=row: self.delete_book(r))
                delete_btn.setMaximumWidth(50)
                delete_btn.setStyleSheet("QPushButton { background-color: #ff4444; }")
                
                btn_layout.addWidget(study_btn)
                btn_layout.addWidget(verify_btn)
                btn_layout.addWidget(edit_btn)
                btn_layout.addWidget(delete_btn)
                btn_layout.addStretch()
                
                self.book_table.setCellWidget(row, 5, btn_widget)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load books: {e}")

    def add_book(self):
        try:
            authors = self.author_controller.get_all_authors()
            if not authors:
                QMessageBox.warning(self, "Warning", "No authors found. Please add an author first")
                return
            
            dialog = BookDialog(authors, self)
            if dialog.exec():
                title = dialog.title_edit.text().strip()
                author_id = dialog.author_combo.currentData()
                desc = dialog.desc_edit.toPlainText().strip()
                
                if not title:
                    QMessageBox.warning(self, "Warning", "Book title is required")
                    return
                
                if not author_id:
                    QMessageBox.warning(self, "Warning", "Author selection is required")
                    return
                
                self.book_controller.add_book(title, author_id, desc)
                self.load_books_table()
                self.popup_signal.emit(f"Book '{title}' added successfully")
        except ValueError as e:
            QMessageBox.warning(self, "Warning", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add book: {e}")

    def edit_book(self, row):
        """Edit a book"""
        try:
            # Get book data
            id_item = self.book_table.item(row, 0)
            if not id_item:
                QMessageBox.warning(self, "Error", "Book ID not found")
                return
            
            book_id = int(id_item.text())
            
            # Get full book data
            books = self.book_controller.get_all_books()
            book_data = None
            for book in books:
                if book['id'] == book_id:
                    book_data = book
                    break
            
            if not book_data:
                QMessageBox.warning(self, "Error", "Book not found")
                return
            
            # Get authors for the dialog
            authors = self.author_controller.get_all_authors()
            
            # Open edit dialog
            from views.book_edit_dialog import BookEditDialog
            dialog = BookEditDialog(book_data, authors, self)
            if dialog.exec():
                data = dialog.get_data()
                self.book_controller.update_book(book_id, **data)
                self.load_books_table()
                self.popup_signal.emit("Book updated successfully")
        
        except ValueError as e:
            QMessageBox.warning(self, "Warning", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Update failed: {e}")

    def show_popup(self, message):
        """Show popup message"""
        QMessageBox.information(self, "Notification", message)

    def update_relations_widget(self):
        """Update the relations widget to refresh authors and relations"""
        if hasattr(self, 'relations_widget'):
            self.relations_widget.load_authors_combo()
            # If an author is selected, refresh relations too
            if self.relations_widget.author_combo.currentData():
                self.relations_widget.load_relations()

    def filter_authors(self, text):
        """Filter authors table based on search text"""
        search_text = text.lower().strip()
        
        for row in range(self.author_table.rowCount()):
            name_item = self.author_table.item(row, 1)  # Name column
            if name_item:
                name = name_item.text().lower()
                if search_text in name:
                    self.author_table.setRowHidden(row, False)
                else:
                    self.author_table.setRowHidden(row, True)
            else:
                self.author_table.setRowHidden(row, True)

    def filter_books(self, text):
        """Filter books table based on search text"""
        search_text = text.lower().strip()
        
        for row in range(self.book_table.rowCount()):
            title_item = self.book_table.item(row, 1)  # Title column
            author_item = self.book_table.item(row, 2)  # Author column
            if title_item and author_item:
                title = title_item.text().lower()
                author = author_item.text().lower()
                if search_text in title or search_text in author:
                    self.book_table.setRowHidden(row, False)
                else:
                    self.book_table.setRowHidden(row, True)
            else:
                self.book_table.setRowHidden(row, True)

    def filter_manuscripts(self, text):
        """Filter manuscripts table based on search text"""
        search_text = text.lower().strip()
        
        for row in range(self.manuscript_table.rowCount()):
            book_item = self.manuscript_table.item(row, 1)  # Book column
            library_item = self.manuscript_table.item(row, 2)  # Library column
            if book_item and library_item:
                book = book_item.text().lower()
                library = library_item.text().lower()
                if search_text in book or search_text in library:
                    self.manuscript_table.setRowHidden(row, False)
                else:
                    self.manuscript_table.setRowHidden(row, True)
            else:
                self.manuscript_table.setRowHidden(row, True)

    def view_author_profile(self, row):
        """View detailed profile for an author"""
        try:
            # Get author data
            id_item = self.author_table.item(row, 0)
            if not id_item:
                QMessageBox.warning(self, "Error", "Author ID not found")
                return
            
            author_id = int(id_item.text())
            name_item = self.author_table.item(row, 1)
            author_name = name_item.text() if name_item else "Unknown"
            
            # Get full author data
            authors = self.author_controller.get_all_authors(limit=1000, offset=0)
            author_data = None
            for author in authors:
                if author['id'] == author_id:
                    author_data = author
                    break
            
            if not author_data:
                QMessageBox.warning(self, "Error", "Author not found")
                return
            
            # Open author profile view
            from views.author_profile_view import AuthorProfileView
            profile_dialog = AuthorProfileView(self.author_controller, author_data)
            profile_dialog.setWindowTitle(f"Author Profile - {author_name}")
            profile_dialog.resize(900, 700)
            profile_dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open author profile: {e}")

    def study_book(self, row):
        """Start study session for a book"""
        try:
            # Get book data
            id_item = self.book_table.item(row, 0)
            if not id_item:
                QMessageBox.warning(self, "Error", "Book ID not found")
                return
            
            book_id = int(id_item.text())
            title_item = self.book_table.item(row, 1)
            book_title = title_item.text() if title_item else "Unknown book"
            
            # Create study session
            from controllers.study_controller import StudyController
            study_controller = StudyController()
            
            try:
                session_id = study_controller.create_study_session(
                    book_id=book_id,
                    duration_minutes=60,
                    notes=f"Study session started for {book_title}"
                )
                self.popup_signal.emit(f"Study session started for '{book_title}' (Session ID: {session_id})")
                self.load_books_table()  # Refresh to show updated studied status
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to start study session: {e}")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to study book: {e}")

    def verify_book(self, row):
        """Verify a book"""
        try:
            # Get book data
            id_item = self.book_table.item(row, 0)
            if not id_item:
                QMessageBox.warning(self, "Error", "Book ID not found")
                return
            
            book_id = int(id_item.text())
            title_item = self.book_table.item(row, 1)
            book_title = title_item.text() if title_item else "Unknown book"
            
            # Update verification status
            from controllers.study_controller import StudyController
            study_controller = StudyController()
            
            try:
                study_controller.update_book_verification_status(
                    book_id=book_id,
                    status='verified',
                    notes=f"Book verified on {datetime.now().strftime('%Y-%m-%d')}"
                )
                self.popup_signal.emit(f"Book '{book_title}' marked as verified")
                self.load_books_table()  # Refresh to show updated status
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to verify book: {e}")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to verify book: {e}")

    def load_manuscripts_table(self):
        """Load manuscripts into the table"""
        try:
            manuscripts = self.manuscript_controller.get_all_manuscripts()
            self.manuscript_table.setRowCount(len(manuscripts))
            for row, manuscript in enumerate(manuscripts):
                self.manuscript_table.setItem(row, 0, QTableWidgetItem(str(manuscript['id'])))
                self.manuscript_table.setItem(row, 1, QTableWidgetItem(manuscript['book_title']))
                self.manuscript_table.setItem(row, 2, QTableWidgetItem(manuscript['library_name']))
                self.manuscript_table.setItem(row, 3, QTableWidgetItem(manuscript['shelf_number']))
                self.manuscript_table.setItem(row, 4, QTableWidgetItem(manuscript['copyist'] or ''))
                
                # Add Edit and Delete buttons
                btn_widget = QWidget()
                btn_layout = QHBoxLayout(btn_widget)
                btn_layout.setContentsMargins(2, 2, 2, 2)
                
                edit_btn = QPushButton("Edit")
                edit_btn.clicked.connect(lambda checked, r=row: self.edit_manuscript(r))
                edit_btn.setMaximumWidth(50)
                
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(lambda checked, r=row: self.delete_manuscript(r))
                delete_btn.setMaximumWidth(50)
                delete_btn.setStyleSheet("QPushButton { background-color: #ff4444; }")
                
                btn_layout.addWidget(edit_btn)
                btn_layout.addWidget(delete_btn)
                btn_layout.addStretch()
                
                self.manuscript_table.setCellWidget(row, 5, btn_widget)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load manuscripts: {e}")

    def add_manuscript(self):
        """Add a new manuscript"""
        try:
            books = self.book_controller.get_all_books()
            if not books:
                QMessageBox.warning(self, "Warning", "No books found. Please add a book first")
                return
            
            from views.manuscript_dialog import ManuscriptDialog
            dialog = ManuscriptDialog(books, self)
            if dialog.exec():
                data = dialog.get_data()
                self.manuscript_controller.add_manuscript(**data)
                self.load_manuscripts_table()
                self.popup_signal.emit(f"Manuscript added successfully")
        except ValueError as e:
            QMessageBox.warning(self, "Warning", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Add failed: {e}")

    def edit_manuscript(self, row):
        """Edit a manuscript"""
        try:
            # Get manuscript data
            id_item = self.manuscript_table.item(row, 0)
            if not id_item:
                QMessageBox.warning(self, "Error", "Manuscript ID not found")
                return
            
            manuscript_id = int(id_item.text())
            manuscripts = self.manuscript_controller.get_all_manuscripts()
            manuscript_data = None
            for manuscript in manuscripts:
                if manuscript['id'] == manuscript_id:
                    manuscript_data = manuscript
                    break
            
            if not manuscript_data:
                QMessageBox.warning(self, "Error", "Manuscript not found")
                return
            
            # Open edit dialog
            books = self.book_controller.get_all_books()
            from views.manuscript_dialog import ManuscriptDialog
            dialog = ManuscriptDialog(books, self, manuscript_data)
            if dialog.exec():
                data = dialog.get_data()
                self.manuscript_controller.update_manuscript(manuscript_id, **data)
                self.load_manuscripts_table()
                self.popup_signal.emit("Manuscript updated successfully")
        
        except ValueError as e:
            QMessageBox.warning(self, "Warning", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Update failed: {e}")

    def delete_manuscript(self, row):
        """Delete a manuscript"""
        try:
            # Get manuscript data
            id_item = self.manuscript_table.item(row, 0)
            if not id_item:
                QMessageBox.warning(self, "Error", "Manuscript ID not found")
                return
            
            manuscript_id = int(id_item.text())
            library_item = self.manuscript_table.item(row, 2)
            library_name = library_item.text() if library_item else "Unknown"
            
            # Confirm deletion
            reply = QMessageBox.question(
                self, 
                "Confirm Delete", 
                f"Are you sure you want to delete manuscript from '{library_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.manuscript_controller.delete_manuscript(manuscript_id)
                self.load_manuscripts_table()
                self.popup_signal.emit(f"Manuscript from '{library_name}' deleted successfully")
        
        except ValueError as e:
            QMessageBox.warning(self, "Warning", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Delete failed: {e}")

    def delete_book(self, row):
        """Delete a book"""
        try:
            # Get book data
            id_item = self.book_table.item(row, 0)
            if not id_item:
                popup_signal.emit("Book ID not found")
                return
            
            book_id = int(id_item.text())
            
            # Get book title for confirmation
            title_item = self.book_table.item(row, 1)
            book_title = title_item.text() if title_item else "Unknown book"
            
            reply = QMessageBox.question(
                self, 
                "Confirm Delete", 
                f"Are you sure you want to delete book '{book_title}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    if self.book_controller.delete_book(book_id):
                        self.load_books_table()
                        self.popup_signal.emit(f"Book '{book_title}' deleted successfully")
                except ValueError as e:
                    if "not found" in str(e).lower():
                        # Book was already deleted, just refresh the table
                        self.load_books_table()
                        self.popup_signal.emit("Book was already removed")
                    else:
                        self.popup_signal.emit(str(e))
                except Exception as e:
                    self.popup_signal.emit(f"Delete failed: {e}")
        
        except ValueError as e:
            self.popup_signal.emit(str(e))
        except Exception as e:
            self.popup_signal.emit(f"Delete failed: {e}")


    def export_authors(self):
        """Export authors to CSV"""
        try:
            authors = self.author_controller.get_all_authors(limit=10000, offset=0)
            from utils.csv_exporter import CSVExporter
            CSVExporter.export_authors(authors, self)
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export authors: {e}")

    def export_books(self):
        """Export books to CSV"""
        try:
            books = self.book_controller.get_all_books(limit=10000, offset=0)
            from utils.csv_exporter import CSVExporter
            CSVExporter.export_books(books, self)
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export books: {e}")

    def export_manuscripts(self):
        """Export manuscripts to CSV"""
        try:
            manuscripts = self.manuscript_controller.get_all_manuscripts(limit=10000, offset=0)
            from utils.csv_exporter import CSVExporter
            CSVExporter.export_manuscripts(manuscripts, self)
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export manuscripts: {e}")
