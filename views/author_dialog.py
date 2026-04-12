from PyQt6.QtWidgets import (QDialog, QFormLayout, QLineEdit, QTextEdit,
                             QDialogButtonBox, QVBoxLayout, QLabel, QMessageBox)
from PyQt6.QtCore import Qt
import re

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
        
        # Validation labels
        self.name_error = QLabel()
        self.birth_error = QLabel()
        self.death_error = QLabel()
        
        # Style error labels
        error_style = "color: red; font-size: 10px;"
        self.name_error.setStyleSheet(error_style)
        self.birth_error.setStyleSheet(error_style)
        self.death_error.setStyleSheet(error_style)

        # Set RTL alignment for Arabic text fields
        self.name_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.bio_edit.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Set placeholders
        self.name_edit.setPlaceholderText("ادخل اسم المؤلف...")
        self.birth_edit.setPlaceholderText("مثلا، 1200")
        self.death_edit.setPlaceholderText("مثلا، 1280")

        form.addRow("الاسم:", self.name_edit)
        form.addRow("", self.name_error)
        form.addRow("سنة الميلاد:", self.birth_edit)
        form.addRow("", self.birth_error)
        form.addRow("سنة الوفاة:", self.death_edit)
        form.addRow("", self.death_error)
        form.addRow("نبذة:", self.bio_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Connect real-time validation
        self.name_edit.textChanged.connect(self.validate_name)
        self.birth_edit.textChanged.connect(self.validate_years)
        self.death_edit.textChanged.connect(self.validate_years)
        
        # Initialize validation state
        self._validation_state = {
            'name': False,
            'years': True  # Years are optional, so valid by default
        }
    
    def validate_name(self, text):
        """Validate author name in real-time"""
        name = text.strip()
        
        if not name:
            self.name_error.setText("الاسم مطلوب")
            self._validation_state['name'] = False
            return False
        
        if len(name) < 2:
            self.name_error.setText("الاسم يجب أن يكون على الأقل 2 أحرف")
            self._validation_state['name'] = False
            return False
        
        if len(name) > 200:
            self.name_error.setText("الاسم طويل جدا")
            self._validation_state['name'] = False
            return False
        
        # Check for dangerous characters
        dangerous_chars = ['<', '>', '&', '\x00', '\x0a', '\x0d']
        for char in dangerous_chars:
            if char in name:
                self.name_error.setText("الاسم يحتوي على أحرف غير صالحة")
                self._validation_state['name'] = False
                return False
        
        # Check for control characters
        if re.search(r'[\x00-\x1f\x7f-\x9f]', name):
            self.name_error.setText("الاسم يحتوي على أحرف تحكم")
            self._validation_state['name'] = False
            return False
        
        self.name_error.setText("")
        self._validation_state['name'] = True
        return True
    
    def validate_years(self):
        """Validate birth and death years"""
        birth_text = self.birth_edit.text().strip()
        death_text = self.death_edit.text().strip()
        
        birth_year = None
        death_year = None
        
        # Validate birth year
        if birth_text:
            if not birth_text.isdigit():
                self.birth_error.setText("سنة الميلاد يجب أن تكون رقم")
                self._validation_state['years'] = False
                return False
            
            birth_year = int(birth_text)
            if birth_year < 0 or birth_year > 3000:
                self.birth_error.setText("سنة الميلاد يجب أن تكون بين 0 و 3000")
                self._validation_state['years'] = False
                return False
        else:
            self.birth_error.setText("")
        
        # Validate death year
        if death_text:
            if not death_text.isdigit():
                self.death_error.setText("سنة الوفاة يجب أن تكون رقم")
                self._validation_state['years'] = False
                return False
            
            death_year = int(death_text)
            if death_year < 0 or death_year > 3000:
                self.death_error.setText("سنة الوفاة يجب أن تكون بين 0 و 3000")
                self._validation_state['years'] = False
                return False
        else:
            self.death_error.setText("")
        
        # Validate logical relationship
        if birth_year and death_year:
            if death_year < birth_year:
                self.death_error.setText("سنة الوفاة لا يمكن أن تكون قبل سنة الميلاد")
                self._validation_state['years'] = False
                return False
        
        self.birth_error.setText("")
        self.death_error.setText("")
        self._validation_state['years'] = True
        return True
    
    def validate_and_accept(self):
        """Validate all fields before accepting"""
        # Run validation on all fields
        name_valid = self.validate_name(self.name_edit.text())
        years_valid = self.validate_years()
        
        # Check bio length
        bio_text = self.bio_edit.toPlainText().strip()
        if len(bio_text) > 10000:
            QMessageBox.warning(self, "خطأ في التحقق", "النبذة طويلة جدا (الحد الأقصى 10000 حرف)")
            return
        
        if not name_valid or not years_valid:
            QMessageBox.warning(self, "خطأ في التحقق", "الرجاء تصحيح الأخطاء قبل المتابعة")
            return
        
        # If all validations pass, accept the dialog
        super().accept()
    
    def get_data(self):
        """Get validated form data"""
        return {
            'name': self.name_edit.text().strip(),
            'birth_year': self.birth_edit.text().strip() or None,
            'death_year': self.death_edit.text().strip() or None,
            'bio': self.bio_edit.toPlainText().strip()
        }
