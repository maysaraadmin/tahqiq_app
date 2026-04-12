from PyQt6.QtWidgets import (QDialog, QFormLayout, QLineEdit, QTextEdit,
                             QDialogButtonBox, QVBoxLayout)

class AuthorEditDialog(QDialog):
    def __init__(self, author_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Author")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.birth_edit = QLineEdit()
        self.death_edit = QLineEdit()
        self.bio_edit = QTextEdit()

        # Pre-fill with existing data
        self.name_edit.setText(author_data['name'])
        self.birth_edit.setText(str(author_data['birth_year']) if author_data['birth_year'] else '')
        self.death_edit.setText(str(author_data['death_year']) if author_data['death_year'] else '')
        self.bio_edit.setPlainText(author_data['bio'] or '')

        form.addRow("Name:", self.name_edit)
        form.addRow("Birth Year:", self.birth_edit)
        form.addRow("Death Year:", self.death_edit)
        form.addRow("Biography:", self.bio_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        """Get the updated data from the form"""
        name = self.name_edit.text().strip()
        birth_year = self.birth_edit.text().strip()
        death_year = self.death_edit.text().strip()
        bio = self.bio_edit.toPlainText().strip()
        
        # Convert empty strings to None for numeric fields
        birth_year = int(birth_year) if birth_year else None
        death_year = int(death_year) if death_year else None
        bio = bio if bio else None
        
        return {
            'name': name if name else None,
            'birth_year': birth_year,
            'death_year': death_year,
            'bio': bio
        }
