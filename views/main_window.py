from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QTabWidget, QLabel, QLineEdit,
                             QFormLayout, QGroupBox, QHeaderView, QSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal
from views.author_dialog import AuthorDialog
from views.book_dialog import BookDialog
from views.relations_widget import RelationsWidget
from controllers.author_controller import AuthorController
from controllers.book_controller import BookController

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.author_controller = AuthorController()
        self.book_controller = BookController()
        
        # Pagination state
        self.current_author_page = 0
        self.current_book_page = 0
        self.page_size = 50  # Default page size
        
        self.setWindowTitle("System for Book Verification and Isnad Tracking")
        self.setGeometry(100, 100, 1000, 700)
        self.setup_ui()
        self.load_authors_table()  # Re-enabled - controllers are working

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # علامات التبويب
        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        # تبويب المؤلفين
        author_tab = QWidget()
        tabs.addTab(author_tab, "المؤلفون")
        self.setup_author_tab(author_tab)

        # تبويب الكتب
        book_tab = QWidget()
        tabs.addTab(book_tab, "الكتب والمخطوطات")
        self.setup_book_tab(book_tab)

        # تبويب العلاقات
        relations_tab = RelationsWidget(self.author_controller)
        tabs.addTab(relations_tab, "الشيوخ والطلاب")

    def setup_author_tab(self, tab):
        layout = QVBoxLayout(tab)

        # شريط أزرار
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("إضافة مؤلف جديد")
        add_btn.clicked.connect(self.add_author)
        delete_btn = QPushButton("حذف المؤلف المحدد")
        delete_btn.clicked.connect(self.delete_author)
        refresh_btn = QPushButton("تحديث")
        refresh_btn.clicked.connect(self.refresh_authors)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # جدول عرض المؤلفين
        self.author_table = QTableWidget()
        self.author_table.setColumnCount(4)
        self.author_table.setHorizontalHeaderLabels(["المعرف", "الاسم", "سنة الميلاد", "سنة الوفاة"])
        self.author_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.author_table)
        
        # Pagination controls
        pagination_layout = QHBoxLayout()
        
        # Previous button
        self.prev_author_btn = QPushButton("السابق")
        self.prev_author_btn.clicked.connect(self.prev_author_page)
        self.prev_author_btn.setEnabled(False)
        
        # Page info
        self.author_page_label = QLabel("صفحة 1 من 1")
        self.author_page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Next button
        self.next_author_btn = QPushButton("التالي")
        self.next_author_btn.clicked.connect(self.next_author_page)
        
        # Page size selector
        pagination_layout.addWidget(QLabel("حجم الصفحة:"))
        self.author_page_size = QSpinBox()
        self.author_page_size.setRange(10, 500)
        self.author_page_size.setValue(self.page_size)
        self.author_page_size.setSingleStep(10)
        self.author_page_size.valueChanged.connect(self.change_author_page_size)
        pagination_layout.addWidget(self.author_page_size)
        
        pagination_layout.addWidget(self.prev_author_btn)
        pagination_layout.addWidget(self.author_page_label)
        pagination_layout.addWidget(self.next_author_btn)
        pagination_layout.addStretch()
        
        layout.addLayout(pagination_layout)

    def load_authors_table(self):
        try:
            print("DEBUG: Starting to load authors table...")
            offset = self.current_author_page * self.page_size
            print(f"DEBUG: Getting authors with limit={self.page_size}, offset={offset}")
            
            authors = self.author_controller.get_all_authors(limit=self.page_size, offset=offset)
            print(f"DEBUG: Retrieved {len(authors)} authors")
            
            self.author_table.setRowCount(len(authors))
            for row, author in enumerate(authors):
                print(f"DEBUG: Adding author {author['name']} to row {row}")
                self.author_table.setItem(row, 0, QTableWidgetItem(str(author['id'])))
                self.author_table.setItem(row, 1, QTableWidgetItem(author['name']))
                self.author_table.setItem(row, 2, QTableWidgetItem(str(author['birth_year'] or '')))
                self.author_table.setItem(row, 3, QTableWidgetItem(str(author['death_year'] or '')))
            
            print("DEBUG: Authors table populated successfully")
            # Update pagination controls
            self.update_author_pagination()
        except Exception as e:
            print(f"DEBUG: Error loading authors: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to load authors: {e}")
    
    def update_author_pagination(self):
        """Update author pagination controls"""
        try:
            total_count = self.author_controller.get_author_count()
            total_pages = (total_count + self.page_size - 1) // self.page_size
            current_page_num = self.current_author_page + 1
            
            self.author_page_label.setText(f"صفحة {current_page_num} من {total_pages}")
            
            # Enable/disable buttons
            self.prev_author_btn.setEnabled(self.current_author_page > 0)
            self.next_author_btn.setEnabled(self.current_author_page < total_pages - 1)
        except Exception as e:
            self.author_page_label.setText("خطأ في تحميل الصفحات")
    
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

    def add_author(self):
        dialog = AuthorDialog(self)
        if dialog.exec():
            name = dialog.name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, "تنبيه", "الاسم مطلوب")
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
                QMessageBox.information(self, "نجاح", f"تمت إضافة المؤلف '{name}' بنجاح")
            except ValueError as e:
                QMessageBox.warning(self, "تنبيه", str(e))
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"فشل الإضافة: {e}")

    def delete_author(self):
        row = self.author_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تنبيه", "الرجاء اختيار مؤلف للحذف")
            return
        
        # Safe null reference check
        id_item = self.author_table.item(row, 0)
        if not id_item:
            QMessageBox.warning(self, "خطأ", "لم يتم العثور على معرف المؤلف")
            return
        
        try:
            author_id = int(id_item.text())
        except (ValueError, TypeError):
            QMessageBox.warning(self, "خطأ", "معرف المؤلف غير صالح")
            return
        
        # Get author name for confirmation
        name_item = self.author_table.item(row, 1)
        author_name = name_item.text() if name_item else "مؤلف غير معروف"
        
        reply = QMessageBox.question(
            self, 
            "Confirm Delete", 
            f"Are you sure you want to delete author '{author_name}'?\nAll books and relations will be deleted.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.author_controller.delete_author(author_id):
                    # Check if current page is empty and go back if needed
                    total_count = self.author_controller.get_author_count()
                    total_pages = (total_count + self.page_size - 1) // self.page_size
                    if self.current_author_page >= total_pages and self.current_author_page > 0:
                        self.current_author_page -= 1
                    
                    self.load_authors_table()
                    QMessageBox.information(self, "Success", f"Author '{author_name}' deleted successfully")
            except ValueError as e:
                QMessageBox.warning(self, "Warning", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Delete failed: {e}")

    def setup_book_tab(self, tab):
        layout = QVBoxLayout(tab)
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("إضافة كتاب")
        add_btn.clicked.connect(self.add_book)
        btn_layout.addWidget(add_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.book_table = QTableWidget()
        self.book_table.setColumnCount(3)
        self.book_table.setHorizontalHeaderLabels(["المعرف", "العنوان", "المؤلف"])
        layout.addWidget(self.book_table)
        self.load_books_table()

    def load_books_table(self):
        try:
            books = self.book_controller.get_all_books()
            self.book_table.setRowCount(len(books))
            for row, book in enumerate(books):
                self.book_table.setItem(row, 0, QTableWidgetItem(str(book.id)))
                self.book_table.setItem(row, 1, QTableWidgetItem(book.title))
                author_name = book.author.name if book.author else 'غير معروف'
                self.book_table.setItem(row, 2, QTableWidgetItem(author_name))
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل الكتب: {e}")

    def add_book(self):
        try:
            authors = self.author_controller.get_all_authors()
            if not authors:
                QMessageBox.warning(self, "تنبيه", "لا يوجد مؤلفون. الرجاء إضافة مؤلف أولاً")
                return
            
            dialog = BookDialog(authors, self)
            if dialog.exec():
                title = dialog.title_edit.text().strip()
                author_id = dialog.author_combo.currentData()
                desc = dialog.desc_edit.toPlainText().strip()
                
                if not title:
                    QMessageBox.warning(self, "تنبيه", "عنوان الكتاب مطلوب")
                    return
                
                if not author_id:
                    QMessageBox.warning(self, "تنبيه", "اختيار المؤلف مطلوب")
                    return
                
                self.book_controller.add_book(title, author_id, desc)
                self.load_books_table()
                QMessageBox.information(self, "نجاح", f"تمت إضافة الكتاب '{title}' بنجاح")
        except ValueError as e:
            QMessageBox.warning(self, "تنبيه", str(e))
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل إضافة الكتاب: {e}")
