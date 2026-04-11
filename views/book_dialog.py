from PyQt6.QtWidgets import (QDialog, QFormLayout, QLineEdit, QTextEdit,
                             QDialogButtonBox, QVBoxLayout, QComboBox)

class BookDialog(QDialog):
    def __init__(self, authors, parent=None):
        super().__init__(parent)
        self.setWindowTitle("كتاب جديد")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.title_edit = QLineEdit()
        self.author_combo = QComboBox()
        self.desc_edit = QTextEdit()

        # ملء قائمة المؤلفين
        for author in authors:
            self.author_combo.addItem(author.name, author.id)

        form.addRow("العنوان:", self.title_edit)
        form.addRow("المؤلف:", self.author_combo)
        form.addRow("الوصف:", self.desc_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
