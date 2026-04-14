from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFormLayout, QGroupBox, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QRegularExpression
from PyQt6.QtGui import QFont, QRegularExpressionValidator
from controllers.auth_controller import auth_controller
import logging

logger = logging.getLogger(__name__)

class SignupDialog(QDialog):
    """Dialog for user registration"""
    
    # Signal emitted when signup is successful
    signup_successful = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Account - Tahqiq")
        self.setModal(True)
        self.setFixedSize(400, 450)
        
        # Setup UI
        self.setup_ui()
        self.setup_validators()
        
        # Center the dialog
        if parent:
            self.move(
                parent.x() + (parent.width() - self.width()) // 2,
                parent.y() + (parent.height() - self.height()) // 2
            )
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Create New Account")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Form group
        form_group = QGroupBox("Account Information")
        form_layout = QFormLayout()
        
        # Username field
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter username (3+ characters)")
        form_layout.addRow("Username:", self.username_edit)
        
        # Email field
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Enter your email address")
        form_layout.addRow("Email:", self.email_edit)
        
        # Full name field
        self.full_name_edit = QLineEdit()
        self.full_name_edit.setPlaceholderText("Enter your full name (optional)")
        form_layout.addRow("Full Name:", self.full_name_edit)
        
        # Password field
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Enter password (6+ characters)")
        form_layout.addRow("Password:", self.password_edit)
        
        # Confirm password field
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_edit.setPlaceholderText("Confirm password")
        form_layout.addRow("Confirm Password:", self.confirm_password_edit)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Password requirements label
        requirements_label = QLabel(
            "Password must contain at least 6 characters, including letters and numbers"
        )
        requirements_label.setWordWrap(True)
        requirements_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(requirements_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.signup_button = QPushButton("Create Account")
        self.signup_button.clicked.connect(self.handle_signup)
        self.signup_button.setDefault(True)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.signup_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def setup_validators(self):
        """Setup input validators"""
        # Username validator (alphanumeric and underscore only)
        username_regex = QRegularExpression(r"[a-zA-Z0-9_]+")
        username_validator = QRegularExpressionValidator(username_regex, self)
        self.username_edit.setValidator(username_validator)
    
    def validate_form(self) -> tuple[bool, str]:
        """Validate the form inputs"""
        username = self.username_edit.text().strip()
        email = self.email_edit.text().strip()
        full_name = self.full_name_edit.text().strip()
        password = self.password_edit.text()
        confirm_password = self.confirm_password_edit.text()
        
        # Check required fields
        if not username:
            return False, "Username is required"
        
        if not email:
            return False, "Email is required"
        
        if not password:
            return False, "Password is required"
        
        if not confirm_password:
            return False, "Please confirm your password"
        
        # Check password match
        if password != confirm_password:
            return False, "Passwords do not match"
        
        return True, ""
    
    def handle_signup(self):
        """Handle signup button click"""
        # Validate form
        is_valid, error_msg = self.validate_form()
        if not is_valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return
        
        # Get form data
        username = self.username_edit.text().strip()
        email = self.email_edit.text().strip()
        full_name = self.full_name_edit.text().strip() or None
        password = self.password_edit.text()
        
        # Disable buttons during signup
        self.signup_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.signup_button.setText("Creating Account...")
        
        # Perform signup
        try:
            success, message = auth_controller.signup(username, email, password, full_name)
            
            if success:
                QMessageBox.information(self, "Success", message)
                self.signup_successful.emit()
                self.accept()
            else:
                QMessageBox.warning(self, "Signup Failed", message)
        
        except Exception as e:
            logger.error(f"Signup dialog error: {e}")
            QMessageBox.critical(self, "Error", "An unexpected error occurred during signup")
        
        finally:
            # Re-enable buttons
            self.signup_button.setEnabled(True)
            self.cancel_button.setEnabled(True)
            self.signup_button.setText("Create Account")
    
    def reset_form(self):
        """Reset the form fields"""
        self.username_edit.clear()
        self.email_edit.clear()
        self.full_name_edit.clear()
        self.password_edit.clear()
        self.confirm_password_edit.clear()
        self.username_edit.setFocus()
