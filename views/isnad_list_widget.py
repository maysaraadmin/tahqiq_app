from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QLabel, QMessageBox, QComboBox, QLineEdit, QGroupBox)
from PyQt6.QtCore import Qt
from controllers.isnad_controller import IsnadController
import os
import logging

logger = logging.getLogger(__name__)

class IsnadListWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.isnad_controller = IsnadController()
        
        self.setup_ui()
        self.load_isnads()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("أسانيد تلقي الكتب")
        title_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; }")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.add_btn = QPushButton("إضافة سند جديد")
        self.add_btn.clicked.connect(self.add_isnad)
        self.add_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px; }")
        header_layout.addWidget(self.add_btn)
        
        refresh_btn = QPushButton("تحديث")
        refresh_btn.clicked.connect(self.load_isnads)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Filter
        filter_group = QGroupBox("تصفية")
        filter_layout = QHBoxLayout(filter_group)
        
        filter_layout.addWidget(QLabel("بحث:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("ابحث عن كتاب أو شيخ...")
        self.search_edit.textChanged.connect(self.load_isnads)
        filter_layout.addWidget(self.search_edit)
        
        layout.addWidget(filter_group)
        
        # Table
        self.isnads_table = QTableWidget()
        self.isnads_table.setColumnCount(6)
        self.isnads_table.setHorizontalHeaderLabels([
            "ID", "Libro", "Autor", "Cadena", "Fecha", "Acciones"
        ])
        self.isnads_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.isnads_table)

    def load_isnads(self):
        try:
            isnads = self.isnad_controller.get_all_isnads()
            
            # Apply search filter
            search_text = self.search_edit.text().lower()
            if search_text:
                filtered = []
                for isnad in isnads:
                    if (search_text in isnad['book_title'].lower() or 
                        search_text in isnad['author_name'].lower()):
                        filtered.append(isnad)
                isnads = filtered
            
            self.isnads_table.setRowCount(len(isnads))
            
            for i, isnad in enumerate(isnads):
                self.isnads_table.setItem(i, 0, QTableWidgetItem(str(isnad['id'])))
                self.isnads_table.setItem(i, 1, QTableWidgetItem(isnad['book_title']))
                self.isnads_table.setItem(i, 2, QTableWidgetItem(isnad['author_name']))
                self.isnads_table.setItem(i, 3, QTableWidgetItem(str(isnad['chain_count'])))
                
                date = isnad['upload_date'][:10] if isnad['upload_date'] else 'N/A'
                self.isnads_table.setItem(i, 4, QTableWidgetItem(date))
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                
                view_btn = QPushButton("عرض")
                view_btn.clicked.connect(lambda checked, data=isnad: self.view_isnad(data))
                view_btn.setMaximumWidth(50)
                actions_layout.addWidget(view_btn)
                
                open_btn = QPushButton("فتح")
                open_btn.clicked.connect(lambda checked, data=isnad: self.open_file(data))
                open_btn.setMaximumWidth(50)
                actions_layout.addWidget(open_btn)
                
                edit_btn = QPushButton("تعديل")
                edit_btn.clicked.connect(lambda checked, data=isnad: self.edit_isnad(data))
                edit_btn.setMaximumWidth(50)
                edit_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; }")
                actions_layout.addWidget(edit_btn)
                
                delete_btn = QPushButton("حذف")
                delete_btn.clicked.connect(lambda checked, data=isnad: self.delete_isnad(data))
                delete_btn.setMaximumWidth(50)
                delete_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
                actions_layout.addWidget(delete_btn)
                
                self.isnads_table.setCellWidget(i, 5, actions_widget)
                
        except Exception as e:
            logger.error(f"Failed to load isnads: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل تحميل الأسانيد: {e}")

    def add_isnad(self):
        from views.isnad_dialog import IsnadDialog
        dialog = IsnadDialog(self)
        dialog.exec()

    def view_isnad(self, isnad_data):
        try:
            details = self.isnad_controller.get_isnad_details(isnad_data['id'])
            
            text = f"تفاصيل السند:\n\n"
            text += f"الكتاب: {details['book_title']}\n"
            text += f"المؤلف: {details['author_name']}\n"
            text += f"الملف: {details['original_filename']}\n"
            text += f"التاريخ: {details['upload_date'][:10] if details['upload_date'] else 'N/A'}\n\n"
            
            text += "سلسلة السند:\n"
            for i, sheikh in enumerate(details['chain']):
                text += f"{i+1}. {sheikh['sheikh_name']}"
                if sheikh['sheikh_description']:
                    text += f" - {sheikh['sheikh_description']}"
                text += "\n"
            
            QMessageBox.information(self, "تفاصيل السند", text)
            
        except Exception as e:
            logger.error(f"Failed to view isnad: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل عرض السند: {e}")

    def open_file(self, isnad_data):
        try:
            file_path = self.isnad_controller.get_isnad_file_path(isnad_data['id'])
            
            import platform
            import subprocess
            
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':
                subprocess.run(['open', file_path])
            else:
                subprocess.run(['xdg-open', file_path])
                
        except Exception as e:
            logger.error(f"Failed to open file: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل فتح الملف: {e}")

    def edit_isnad(self, isnad_data):
        """Edit existing isnad"""
        try:
            from views.isnad_dialog import IsnadDialog
            
            # Get full isnad details
            details = self.isnad_controller.get_isnad_details(isnad_data['id'])
            
            # Create dialog for editing
            dialog = IsnadDialog(self)
            
            # Set existing data
            dialog.current_book_id = details['book_id']
            dialog.uploaded_file_path = details['file_path']
            dialog.isnad_chain = details['chain']
            
            # Set book info
            for i in range(dialog.author_combo.count()):
                if dialog.author_combo.itemData(i) == details['book_id']:
                    dialog.author_combo.setCurrentIndex(i)
                    break
            
            dialog.on_author_changed()
            for i in range(dialog.book_combo.count()):
                if dialog.book_combo.itemData(i) == details['book_id']:
                    dialog.book_combo.setCurrentIndex(i)
                    break
            
            dialog.title_edit.setText(details['book_title'])
            dialog.description_edit.setPlainText(details['book_description'])
            dialog.file_label.setText(f"الملف: {details['original_filename']}")
            dialog.file_label.setStyleSheet("QLabel { color: green; }")
            
            # Update isnad display
            dialog.update_isnad_display()
            dialog.update_isnad_table()
            dialog.check_save_conditions()
            
            # Change dialog title
            dialog.setWindowTitle("تعديل سند تلقي الكتاب")
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_isnads()
                
        except Exception as e:
            logger.error(f"Failed to edit isnad: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل تعديل السند: {e}")

    def delete_isnad(self, isnad_data):
        """Delete isnad"""
        reply = QMessageBox.question(
            self, 
            "تأكيد الحذف",
            f"هل تريد حذف سند كتاب '{isnad_data['book_title']}'؟\n\nهذا الإجراء لا يمكن التراجع عنه.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            self.isnad_controller.delete_isnad(isnad_data['id'])
            QMessageBox.information(self, "نجاح", "تم حذف السند بنجاح")
            self.load_isnads()
            
        except Exception as e:
            logger.error(f"Failed to delete isnad: {e}")
            QMessageBox.critical(self, "خطأ", f"فشل حذف السند: {e}")
