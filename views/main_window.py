from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QTabWidget, QHeaderView, QSpinBox,
                             QLabel, QLineEdit, QMenuBar, QMenu, QDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from datetime import datetime
from views.author_dialog import AuthorDialog
from views.book_dialog import BookDialog
from views.relations_widget import RelationsWidget
from views.login_dialog import LoginDialog
from views.signup_dialog import SignupDialog
from views.profile_dialog import ProfileDialog
from controllers.author_controller import AuthorController
from controllers.book_controller import BookController
from controllers.manuscript_controller import ManuscriptController
from controllers.auth_controller import auth_controller
from utils.async_worker import LoadDataWorker, DatabaseOperationWorker
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
        
        # Async worker and thread tracking
        self._current_worker = None
        self._current_thread = None
        
        # Hide main window initially
        self.hide()
        
        # Check authentication first
        if not self.check_authentication():
            return
        
        # Only setup UI after successful authentication
        self.setup_ui()
        self.setup_menu()
        self.load_authors_table()
        
        # Connect popup signal to show messages
        self.popup_signal.connect(self.show_popup)
        
        # Show main window after everything is ready
        self.show()
        
        # Cleanup on close
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

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
        self.investigation_widget = self.setup_investigation_tab()
        tabs.addTab(self.investigation_widget, "Investigation")
        self.isnad_widget = self.setup_isnad_tab()
        tabs.addTab(self.isnad_widget, "Isnad")
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
        
        # User menu (authentication)
        user_menu = menubar.addMenu("User")
        
        current_user = auth_controller.get_current_user()
        if current_user:
            # Profile action
            profile_action = user_menu.addAction("Profile")
            profile_action.triggered.connect(self.show_profile_dialog)
            
            # Logout action
            logout_action = user_menu.addAction("Logout")
            logout_action.triggered.connect(self.handle_logout)
        else:
            # Login action
            login_action = user_menu.addAction("Login")
            login_action.triggered.connect(self.show_login_dialog)
            
            # Signup action
            signup_action = user_menu.addAction("Create Account")
            signup_action.triggered.connect(self.show_signup_dialog)
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # Backup actions
        backup_action = file_menu.addAction("Create Backup")
        backup_action.triggered.connect(self.create_backup)
        
        restore_action = file_menu.addAction("Restore Backup")
        restore_action.triggered.connect(self.restore_backup)
        
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
                         "Tahqiq App - Research Management System\n\n"
                         "Version 1.0.0\n\n"
                         "Features:\n"
                         " Author, Book, and Manuscript management\n"
                         " Sheikh-Student relationship tracking\n"
                         " Study session management\n"
                         " Database backup and restore\n"
                         " Arabic RTL support")

    def load_authors_table(self):
        """Load authors into table asynchronously"""
        self._set_table_loading(self.author_table, True)
        
        # Create worker for async loading
        worker = LoadDataWorker(self.author_controller, 'get_all_authors')
        worker.finished.connect(self._on_authors_loaded)
        worker.error.connect(self._on_authors_load_error)
        
        # Start worker in background thread
        self._current_worker = worker
        self._current_thread = QThread()
        worker.moveToThread(self._current_thread)
        
        # Connect thread started signal to start work
        self._current_thread.started.connect(worker.start_work)
        # Connect thread finished signal to cleanup
        self._current_thread.finished.connect(self._on_thread_finished)
        
        # Start the thread
        self._current_thread.start()
    
    def _on_authors_loaded(self, authors):
        """Handle successful author loading"""
        self._set_table_loading(self.author_table, False)
        
        self.author_table.setRowCount(len(authors))
        for row, author in enumerate(authors):
            self.author_table.setItem(row, 0, QTableWidgetItem(str(author['id'])))
            self.author_table.setItem(row, 1, QTableWidgetItem(author['name']))
            self.author_table.setItem(row, 2, QTableWidgetItem(str(author['birth_year'] or '')))
            self.author_table.setItem(row, 3, QTableWidgetItem(str(author['death_year'] or '')))
            self.author_table.setItem(row, 4, QTableWidgetItem(author['bio'] or ''))
        
        self._current_worker = None
        if self._current_thread:
            self._current_thread.quit()
            self._current_thread.wait()
            self._current_thread = None
        logger.info(f"Loaded {len(authors)} authors asynchronously")
    
    def _on_authors_load_error(self, error_message):
        """Handle author loading error"""
        self._set_table_loading(self.author_table, False)
        self._current_worker = None
        if self._current_thread:
            self._current_thread.quit()
            self._current_thread.wait()
            self._current_thread = None
        logger.error(f"POPUP_ERROR: Failed to load authors: {error_message}")
        self.show_error(f"Failed to load authors: {error_message}")
    
    def _set_table_loading(self, table, loading):
        """Set table loading state"""
        if loading:
            table.setRowCount(0)
            table.setItem(0, 0, QTableWidgetItem("Loading..."))
            table.setSpan(0, 0, 1, table.columnCount() - 1)
        else:
            # Clear loading indicator
            if table.item(0, 0) and table.item(0, 0).text() == "Loading...":
                table.setRowCount(0)
                table.clearContents()

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
                logger.warning("POPUP_WARNING: Name is required")
                self.show_warning("Name is required")
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
                logger.info(f"POPUP_SUCCESS: Author '{name}' added successfully")
                self.popup_signal.emit(f"Author '{name}' added successfully")
            except ValueError as e:
                logger.warning(f"POPUP_WARNING: {str(e)}")
                self.show_warning(str(e))
            except Exception as e:
                logger.error(f"POPUP_ERROR: Add failed: {e}")
                self.show_error(f"Add failed: {e}")

    def edit_author(self, row):
        """Edit an author"""
        try:
            # Get author data
            id_item = self.author_table.item(row, 0)
            if not id_item:
                self.show_warning("Author ID not found")
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
                self.show_warning("Author not found")
                return
            
            # Open edit dialog
            from views.author_edit_dialog import AuthorEditDialog
            dialog = AuthorEditDialog(author_data, self)
            if dialog.exec():
                data = dialog.get_data()
                self.author_controller.update_author(author_id, **data)
                self.load_authors_table()
                self.update_relations_widget()  # Update relations widget
                logger.info("POPUP_SUCCESS: Author updated successfully")
                self.popup_signal.emit("Author updated successfully")
        
        except ValueError as e:
            self.show_warning(str(e))
        except Exception as e:
            self.show_error(f"Update failed: {e}")

    def delete_author(self, row=None):
        """Delete an author"""
        if row is None:
            row = self.author_table.currentRow()
        
        if row < 0:
            self.show_warning("Please select an author to delete")
            return
        
        # Safe null reference check
        id_item = self.author_table.item(row, 0)
        if not id_item:
            self.show_warning("Author ID not found")
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
                reply = self.show_question(
                    "Cascade Delete Required",
                    f"{str(e)}\n\nDo you want to delete all linked data (books and relations)?\n\nThis action cannot be undone."
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        self.author_controller.delete_author(author_id, cascade_delete=True)
                        self.load_authors_table()
                        self.load_books_table()  # Refresh books table too
                        self.update_relations_widget()
                        self.popup_signal.emit(f"Author '{author_name}' and all linked data deleted successfully")
                    except Exception as cascade_error:
                        self.show_error(f"Cascade delete failed: {cascade_error}")
            else:
                # Other validation error
                self.show_warning(str(e))
        except Exception as e:
            self.show_error(f"Delete failed: {e}")

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
                study_btn.setStyleSheet("QPushButton { background-color: #27ae60; color: white; padding: 2px; }")
                study_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                
                verify_btn = QPushButton("Verify")
                verify_btn.clicked.connect(lambda checked, r=row: self.verify_book(r))
                verify_btn.setMaximumWidth(50)
                verify_btn.setStyleSheet("QPushButton { background-color: #f39c12; color: white; padding: 2px; }")
                verify_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                
                edit_btn = QPushButton("Edit")
                edit_btn.clicked.connect(lambda checked, r=row: self.edit_book(r))
                edit_btn.setMaximumWidth(50)
                edit_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; padding: 2px; }")
                edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(lambda checked, r=row: self.delete_book(r))
                delete_btn.setMaximumWidth(50)
                delete_btn.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; padding: 2px; }")
                delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                
                btn_layout.addWidget(study_btn)
                btn_layout.addWidget(verify_btn)
                btn_layout.addWidget(edit_btn)
                btn_layout.addWidget(delete_btn)
                btn_layout.addStretch()
                
                self.book_table.setCellWidget(row, 5, btn_widget)
        except Exception as e:
            self.show_error(f"Failed to load books: {e}")

    def add_book(self):
        try:
            authors = self.author_controller.get_all_authors()
            if not authors:
                self.show_warning("No authors found. Please add an author first")
                return
            
            dialog = BookDialog(authors, self)
            if dialog.exec():
                title = dialog.title_edit.text().strip()
                author_id = dialog.author_combo.currentData()
                desc = dialog.desc_edit.toPlainText().strip()
                
                if not title:
                    self.show_warning("Book title is required")
                    return
                
                if not author_id:
                    self.show_warning("Author selection is required")
                    return
                
                self.book_controller.add_book(title, author_id, desc)
                self.load_books_table()
                self.popup_signal.emit(f"Book '{title}' added successfully")
        except ValueError as e:
            self.show_warning(str(e))
        except Exception as e:
            self.show_error(f"Failed to add book: {e}")

    def edit_book(self, row):
        """Edit a book"""
        try:
            # Get book data
            id_item = self.book_table.item(row, 0)
            if not id_item:
                self.show_warning("Book ID not found")
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
                self.show_warning("Book not found")
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
            self.show_warning(str(e))
        except Exception as e:
            self.show_error(f"Update failed: {e}")

    def show_popup(self, message):
        """Show popup message"""
        logger.info(f"POPUP: {message}")
        QMessageBox.information(self, "Notification", message)
    
    def show_warning(self, message):
        """Show warning popup with logging"""
        logger.warning(f"POPUP_WARNING: {message}")
        QMessageBox.warning(self, "Warning", message)
    
    def show_error(self, message):
        """Show error popup with logging"""
        logger.error(f"POPUP_ERROR: {message}")
        QMessageBox.critical(self, "Error", message)
    
    def show_question(self, title, message):
        """Show question popup with logging"""
        logger.info(f"POPUP_QUESTION: {title} - {message}")
        reply = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply

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
                self.show_warning("Author ID not found")
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
                self.show_warning("Author not found")
                return
            
            # Open author profile view
            from views.author_profile_view import AuthorProfileView
            profile_dialog = AuthorProfileView(self.author_controller, author_data)
            profile_dialog.setWindowTitle(f"Author Profile - {author_name}")
            profile_dialog.resize(900, 700)
            profile_dialog.exec()
            
        except Exception as e:
            self.show_error(f"Failed to open author profile: {e}")

    def study_book(self, row):
        """Start study session for a book"""
        try:
            # Get book data
            id_item = self.book_table.item(row, 0)
            if not id_item:
                self.show_warning("Book ID not found")
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
                self.show_error(f"Failed to start study session: {e}")
        
        except Exception as e:
            self.show_error(f"Failed to study book: {e}")

    def verify_book(self, row):
        """Verify a book"""
        try:
            # Get book data
            id_item = self.book_table.item(row, 0)
            if not id_item:
                self.show_warning("Book ID not found")
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
                self.show_error(f"Failed to verify book: {e}")
        
        except Exception as e:
            self.show_error(f"Failed to verify book: {e}")

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
            self.show_error(f"Failed to load manuscripts: {e}")

    def add_manuscript(self):
        """Add a new manuscript"""
        try:
            books = self.book_controller.get_all_books()
            if not books:
                self.show_warning("No books found. Please add a book first")
                return
            
            from views.manuscript_dialog import ManuscriptDialog
            dialog = ManuscriptDialog(books, self)
            if dialog.exec():
                data = dialog.get_data()
                self.manuscript_controller.add_manuscript(**data)
                self.load_manuscripts_table()
                self.popup_signal.emit(f"Manuscript added successfully")
        except ValueError as e:
            self.show_warning(str(e))
        except Exception as e:
            self.show_error(f"Add failed: {e}")

    def edit_manuscript(self, row):
        """Edit a manuscript"""
        try:
            # Get manuscript data
            id_item = self.manuscript_table.item(row, 0)
            if not id_item:
                self.show_warning("Manuscript ID not found")
                return
            
            manuscript_id = int(id_item.text())
            manuscripts = self.manuscript_controller.get_all_manuscripts()
            manuscript_data = None
            for manuscript in manuscripts:
                if manuscript['id'] == manuscript_id:
                    manuscript_data = manuscript
                    break
            
            if not manuscript_data:
                self.show_warning("Manuscript not found")
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
            self.show_warning(str(e))
        except Exception as e:
            self.show_error(f"Update failed: {e}")

    def delete_manuscript(self, row):
        """Delete a manuscript"""
        try:
            # Get manuscript data
            id_item = self.manuscript_table.item(row, 0)
            if not id_item:
                self.show_warning("Manuscript ID not found")
                return
            
            manuscript_id = int(id_item.text())
            manuscripts = self.manuscript_controller.get_all_manuscripts()
            manuscript_data = None
            for manuscript in manuscripts:
                if manuscript['id'] == manuscript_id:
                    manuscript_data = manuscript
                    break
            
            if not manuscript_data:
                self.show_warning("Manuscript not found")
                return
            
            # Get manuscript details for confirmation
            library_item = self.manuscript_table.item(row, 2)
            library_name = library_item.text() if library_item else "Unknown"
            
            reply = self.show_question(
                "Confirm Delete",
                f"Are you sure you want to delete manuscript from '{library_name}'?"
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.manuscript_controller.delete_manuscript(manuscript_id)
                self.load_manuscripts_table()
                self.popup_signal.emit(f"Manuscript from '{library_name}' deleted successfully")
        
        except ValueError as e:
            self.show_warning(str(e))
        except Exception as e:
            self.show_error(f"Delete failed: {e}")

    def delete_book(self, row):
        """Delete a book"""
        try:
            # Get book data
            id_item = self.book_table.item(row, 0)
            if not id_item:
                self.show_warning("Book ID not found")
                return
            
            book_id = int(id_item.text())
            
            # Get book title for confirmation
            title_item = self.book_table.item(row, 1)
            book_title = title_item.text() if title_item else "Unknown book"
            
            reply = self.show_question(
                "Confirm Delete",
                f"Are you sure you want to delete book '{book_title}'?"
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


    
    def _on_thread_finished(self):
        """Handle thread completion"""
        logger.debug("Background thread finished")

    def closeEvent(self, event):
        """Handle window close event with proper cleanup"""
        try:
            # Cancel any running worker
            if self._current_worker and hasattr(self._current_worker, 'is_running') and self._current_worker.is_running():
                logger.info("Cancelling running worker...")
                self._current_worker._is_running = False
            
            # Stop and cleanup thread
            if self._current_thread:
                if self._current_thread.isRunning():
                    logger.info("Stopping background thread...")
                    self._current_thread.quit()
                    self._current_thread.wait(3000)  # Wait up to 3 seconds
                self._current_thread = None
            
            # Clear worker reference
            self._current_worker = None
            
            logger.info("MainWindow cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during MainWindow cleanup: {e}")
        
        # Accept the close event
        event.accept()
    
    def check_authentication(self):
        """Check if user is authenticated, show login dialog if not"""
        if not auth_controller.is_logged_in():
            # Show login dialog
            login_dialog = LoginDialog(self)
            login_dialog.login_successful.connect(self.on_login_successful)
            
            result = login_dialog.exec()
            
            # If login was cancelled, close the main window
            if result == QDialog.DialogCode.Rejected:
                self.close()
                return False
            # If login dialog was closed without login, also close main window
            elif result != QDialog.DialogCode.Accepted or not auth_controller.is_logged_in():
                self.close()
                return False
        
        return True
    
    def on_login_successful(self):
        """Handle successful login"""
        current_user = auth_controller.get_current_user()
        if current_user:
            logger.info(f"User {current_user.username} logged in successfully")
            self.update_window_title()
    
    def update_window_title(self):
        """Update window title with current user info"""
        current_user = auth_controller.get_current_user()
        if current_user:
            self.setWindowTitle(f"Tahqiq App - {current_user.username}")
        else:
            self.setWindowTitle("Tahqiq App")
    
        
    def show_login_dialog(self):
        """Show login dialog"""
        login_dialog = LoginDialog(self)
        login_dialog.login_successful.connect(self.on_login_successful)
        login_dialog.exec()
    
    def show_signup_dialog(self):
        """Show signup dialog"""
        signup_dialog = SignupDialog(self)
        signup_dialog.signup_successful.connect(self.on_signup_successful)
        signup_dialog.exec()
    
    def on_signup_successful(self):
        """Handle successful signup"""
        QMessageBox.information(self, "Success", 
                              "Account created successfully! Please login to continue.")
        self.show_login_dialog()
    
    def show_profile_dialog(self):
        """Show user profile dialog"""
        profile_dialog = ProfileDialog(self)
        profile_dialog.profile_updated.connect(self.on_profile_updated)
        profile_dialog.exec()
    
    def on_profile_updated(self):
        """Handle profile update"""
        self.update_window_title()
        QMessageBox.information(self, "Success", "Profile updated successfully!")
    
    def handle_logout(self):
        """Handle logout action"""
        reply = QMessageBox.question(
            self, "Confirm Logout", 
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success, message = auth_controller.logout()
                if success:
                    QMessageBox.information(self, "Success", message)
                    # Check authentication again (will show login dialog)
                    self.check_authentication()
                else:
                    QMessageBox.warning(self, "Logout Failed", message)
            except Exception as e:
                logger.error(f"Logout error: {e}")
                QMessageBox.critical(self, "Error", "An unexpected error occurred")

    def setup_investigation_tab(self):
        """Setup investigation tab for book research and manuscript comparison"""
        from views.investigation_list_widget import InvestigationListWidget
        widget = InvestigationListWidget(self)
        return widget

    def show_investigation_dialog(self):
        """Show investigation dialog for selected book"""
        from views.book_selection_dialog import BookSelectionDialog
        
        dialog = BookSelectionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            investigation_data = dialog.get_investigation_data()
            if investigation_data:
                self.open_investigation(investigation_data)

    def open_investigation(self, investigation_data):
        """Open investigation dialog with provided data"""
        from views.investigation_dialog import InvestigationDialog
        
        dialog = InvestigationDialog(investigation_data, self)
        dialog.exec()

    def setup_isnad_tab(self):
        """Setup isnad tab for book transmission chains"""
        from views.isnad_list_widget import IsnadListWidget
        widget = IsnadListWidget(self)
        return widget
