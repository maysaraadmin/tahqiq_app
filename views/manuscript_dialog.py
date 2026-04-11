from PyQt6.QtWidgets import (QDialog, QFormLayout, QLineEdit, QTextEdit,
                             QDialogButtonBox, QVBoxLayout, QComboBox)

class ManuscriptDialog(QDialog):
    def __init__(self, books, parent=None):
        super().__init__(parent)
        self.setWindowTitle("مخطوط جديد")
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
            self.book_combo.addItem(book.title, book.id)

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
