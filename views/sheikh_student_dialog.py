from PyQt6.QtWidgets import (QDialog, QFormLayout, QComboBox, QLineEdit,
                             QDialogButtonBox, QVBoxLayout, QRadioButton,
                             QButtonGroup, QHBoxLayout, QMessageBox)

class SheikhStudentDialog(QDialog):
    def __init__(self, controller, current_author_id, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.current_author_id = current_author_id
        self.setWindowTitle("إضافة علاقة شيخ / طالب")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # اختيار نوع العلاقة
        type_layout = QHBoxLayout()
        self.relation_group = QButtonGroup()
        self.sheikh_radio = QRadioButton("شيخ (تلقى عنه العلم)")
        self.student_radio = QRadioButton("طالب (تتلمذ عليه)")
        self.sheikh_radio.setChecked(True)
        self.relation_group.addButton(self.sheikh_radio)
        self.relation_group.addButton(self.student_radio)
        type_layout.addWidget(self.sheikh_radio)
        type_layout.addWidget(self.student_radio)
        form.addRow("نوع العلاقة:", type_layout)

        # اختيار الشخص الآخر
        self.person_combo = QComboBox()
        self.load_persons()
        form.addRow("الشخص:", self.person_combo)

        # نوع العلاقة (سماع، إجازة...)
        self.relation_type_edit = QLineEdit()
        form.addRow("نوع التلقي:", self.relation_type_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_persons(self):
        try:
            authors = self.controller.get_all_authors()
            
            self.person_combo.clear()
            
            # Filter out current author
            other_authors = [author for author in authors if author['id'] != self.current_author_id]
            
            if not other_authors:
                # No other authors available
                self.person_combo.addItem("No other authors available", None)
                self.person_combo.setEnabled(False)
            else:
                # Add other authors to combo
                for author in other_authors:
                    self.person_combo.addItem(author['name'], author['id'])
                self.person_combo.setEnabled(True)
                
        except Exception as e:
            self.person_combo.addItem("Error loading authors", None)
            self.person_combo.setEnabled(False)

    def accept(self):
        other_id = self.person_combo.currentData()
        if not other_id:
            if self.person_combo.count() == 1 and "No other authors" in self.person_combo.itemText(0):
                QMessageBox.information(self, "Info", "You need at least 2 authors to create relations.\nPlease add another author first.")
            else:
                QMessageBox.warning(self, "Error", "Please select a person")
            return  # Don't call super().accept()
        
        rel_type = self.relation_type_edit.text().strip()
        
        try:
            if self.sheikh_radio.isChecked():
                # Other person is sheikh, current author is student
                self.controller.add_sheikh_relation(self.current_author_id, other_id, rel_type)
            else:
                # Other person is student, current author is sheikh
                self.controller.add_sheikh_relation(other_id, self.current_author_id, rel_type)
            super().accept()
        except ValueError as e:
            QMessageBox.warning(self, "Warning", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add relation: {e}")
