from PyQt6.QtWidgets import (QDialog, QFormLayout, QLineEdit, QTextEdit,
                             QDialogButtonBox, QVBoxLayout, QComboBox, QMessageBox)

class ManuscriptDialog(QDialog):
    def __init__(self, books, parent=None, manuscript_data=None):
        super().__init__(parent)
        self.setWindowTitle("مخطوط جديد" if not manuscript_data else "تعديل مخطوط")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.book_combo = QComboBox()
        self.library_edit = QLineEdit()
        self.shelf_edit = QLineEdit()
        self.copyist_edit = QLineEdit()
        self.copy_date_edit = QLineEdit()
        self.notes_edit = QTextEdit()

        # ملء قائمة الكتب
        for book in books:
            self.book_combo.addItem(book['title'], book['id'])

        form.addRow("الكتاب:", self.book_combo)
        form.addRow("اسم المكتبة:", self.library_edit)
        form.addRow("رقم الرف:", self.shelf_edit)
        form.addRow("الناسخ:", self.copyist_edit)
        form.addRow("تاريخ النسخ:", self.copy_date_edit)
        form.addRow("ملاحظات:", self.notes_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Pre-fill data if editing
        if manuscript_data:
            self.set_manuscript_data(manuscript_data)

    def set_manuscript_data(self, data):
        """Pre-fill form with existing manuscript data"""
        # Set book selection
        for i in range(self.book_combo.count()):
            if self.book_combo.itemData(i) == data['book_id']:
                self.book_combo.setCurrentIndex(i)
                break
        
        self.library_edit.setText(data.get('library_name', ''))
        self.shelf_edit.setText(data.get('shelf_number', ''))
        self.copyist_edit.setText(data.get('copyist', ''))
        self.copy_date_edit.setText(data.get('copy_date', ''))
        self.notes_edit.setText(data.get('notes', ''))

    def get_data(self):
        """Get form data as dictionary"""
        return {
            'book_id': self.book_combo.currentData(),
            'library_name': self.library_edit.text().strip(),
            'shelf_number': self.shelf_edit.text().strip(),
            'copyist': self.copyist_edit.text().strip() or None,
            'copy_date': self.copy_date_edit.text().strip() or None,
            'notes': self.notes_edit.toPlainText().strip() or None
        }
    
    def cleanup(self):
        """Clean up dialog resources"""
        self.book_combo.clear()
        self.library_edit.clear()
        self.shelf_edit.clear()
        self.copyist_edit.clear()
        self.copy_date_edit.clear()
        self.notes_edit.clear()
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()

    def accept(self):
        """Validate and accept the dialog"""
        data = self.get_data()
        
        # Validate required fields
        if not data['library_name']:
            QMessageBox.warning(self, "خطأ في التحقق", "اسم المكتبة مطلوب")
            return
        
        if not data['shelf_number']:
            QMessageBox.warning(self, "خطأ في التحقق", "رقم الرف مطلوب")
            return
        
        if not data['book_id']:
            QMessageBox.warning(self, "خطأ في التحقق", "الرجاء اختيار كتاب")
            return
        
        super().accept()
