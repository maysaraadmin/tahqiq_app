from PyQt6.QtWidgets import (QDialog, QFormLayout, QLineEdit, QTextEdit,
                             QDialogButtonBox, QVBoxLayout, QComboBox)

class BookEditDialog(QDialog):
    def __init__(self, book_data, authors, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Book")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.title_edit = QLineEdit()
        self.author_combo = QComboBox()
        self.desc_edit = QTextEdit()

        # Fill author list
        for author in authors:
            self.author_combo.addItem(author['name'], author['id'])

        # Pre-fill with existing data
        self.title_edit.setText(book_data['title'])
        self.desc_edit.setPlainText(book_data['description'] or '')
        
        # Set current author
        for i in range(self.author_combo.count()):
            if self.author_combo.itemData(i) == book_data['author_id']:
                self.author_combo.setCurrentIndex(i)
                break

        form.addRow("Title:", self.title_edit)
        form.addRow("Author:", self.author_combo)
        form.addRow("Description:", self.desc_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        """Get the updated data from the form"""
        title = self.title_edit.text().strip()
        author_id = self.author_combo.currentData()
        description = self.desc_edit.toPlainText().strip()
        
        return {
            'title': title if title else None,
            'author_id': author_id,
            'description': description if description else None
        }
