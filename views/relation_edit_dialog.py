from PyQt6.QtWidgets import (QDialog, QFormLayout, QLineEdit, QComboBox,
                             QDialogButtonBox, QVBoxLayout, QLabel)

class RelationEditDialog(QDialog):
    def __init__(self, relation_data, authors, current_author_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Relation")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.student_combo = QComboBox()
        self.sheikh_combo = QComboBox()
        self.relation_type_edit = QLineEdit()

        # Fill author lists (exclude current author to prevent self-relations)
        for author in authors:
            if author['id'] != current_author_id:
                self.student_combo.addItem(author['name'], author['id'])
                self.sheikh_combo.addItem(author['name'], author['id'])

        # Pre-fill with existing data
        self.relation_type_edit.setText(relation_data['relation_type'] or '')
        
        # Set current student and sheikh
        for i in range(self.student_combo.count()):
            if self.student_combo.itemData(i) == relation_data['student_id']:
                self.student_combo.setCurrentIndex(i)
                break
                
        for i in range(self.sheikh_combo.count()):
            if self.sheikh_combo.itemData(i) == relation_data['sheikh_id']:
                self.sheikh_combo.setCurrentIndex(i)
                break

        form.addRow("Student:", self.student_combo)
        form.addRow("Sheikh:", self.sheikh_combo)
        form.addRow("Relation Type:", self.relation_type_edit)
        
        # Add info label
        info_label = QLabel("Note: Relation type can be 'Reading', 'Listening', 'Ijaza', etc.")
        info_label.setWordWrap(True)
        form.addRow("", info_label)
        
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def validate_and_accept(self):
        """Validate before accepting"""
        student_id = self.student_combo.currentData()
        sheikh_id = self.sheikh_combo.currentData()
        
        if student_id == sheikh_id:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Warning", "Student and Sheikh cannot be the same person!")
            return
        
        self.accept()

    def get_data(self):
        """Get the updated data from the form"""
        student_id = self.student_combo.currentData()
        sheikh_id = self.sheikh_combo.currentData()
        relation_type = self.relation_type_edit.text().strip()
        
        return {
            'student_id': student_id,
            'sheikh_id': sheikh_id,
            'relation_type': relation_type if relation_type else ''
        }
