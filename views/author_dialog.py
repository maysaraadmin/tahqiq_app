from PyQt6.QtWidgets import (QDialog, QFormLayout, QLineEdit, QTextEdit,
                             QDialogButtonBox, QVBoxLayout)
from PyQt6.QtCore import Qt

class AuthorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("مؤلف جديد")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.birth_edit = QLineEdit()
        self.death_edit = QLineEdit()
        self.bio_edit = QTextEdit()

        # Set RTL alignment for Arabic text fields
        self.name_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.bio_edit.setAlignment(Qt.AlignmentFlag.AlignRight)

        form.addRow("الاسم:", self.name_edit)
        form.addRow("سنة الميلاد:", self.birth_edit)
        form.addRow("سنة الوفاة:", self.death_edit)
        form.addRow("نبذة:", self.bio_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
