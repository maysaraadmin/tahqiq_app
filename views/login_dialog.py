from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFormLayout, QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from controllers.auth_controller import auth_controller
import logging

logger = logging.getLogger(__name__)

class LoginDialog(QDialog):
    """Dialog for user login"""
    
    # Signal emitted when login is successful
    login_successful = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login - Tahqiq")
        self.setModal(True)
        self.setFixedSize(350, 300)
        
        # Setup UI
        self.setup_ui()
        
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
        title_label = QLabel("Login to Your Account")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Form group
        form_group = QGroupBox("Login Information")
        form_layout = QFormLayout()
        
        # Username/Email field
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Username or Email")
        form_layout.addRow("Username/Email:", self.username_edit)
        
        # Password field
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Enter your password")
        form_layout.addRow("Password:", self.password_edit)
        
        # Remember me checkbox
        self.remember_checkbox = QCheckBox("Remember me")
        form_layout.addRow("", self.remember_checkbox)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.handle_login)
        self.login_button.setDefault(True)
        
        self.signup_button = QPushButton("Create Account")
        self.signup_button.clicked.connect(self.show_signup)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.signup_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Forgot password link (placeholder for future implementation)
        forgot_label = QLabel("Forgot password?")
        forgot_label.setStyleSheet("color: blue; text-decoration: underline;")
        forgot_label.setCursor(Qt.CursorShape.PointingHandCursor)
        # forgot_label.mousePressEvent = self.show_forgot_password  # Future implementation
        layout.addWidget(forgot_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.setLayout(layout)
    
    def validate_form(self) -> tuple[bool, str]:
        """Validate the form inputs"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        
        if not username:
            return False, "Username or email is required"
        
        if not password:
            return False, "Password is required"
        
        return True, ""
    
    def handle_login(self):
        """Handle login button click"""
        # Validate form
        is_valid, error_msg = self.validate_form()
        if not is_valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return
        
        # Get form data
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        
        # Disable buttons during login
        self.login_button.setEnabled(False)
        self.signup_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.login_button.setText("Logging in...")
        
        # Perform login
        try:
            success, message = auth_controller.login(username, password)
            
            if success:
                QMessageBox.information(self, "Success", message)
                self.login_successful.emit()
                self.accept()
            else:
                QMessageBox.warning(self, "Login Failed", message)
                self.password_edit.clear()
                self.password_edit.setFocus()
        
        except Exception as e:
            logger.error(f"Login dialog error: {e}")
            QMessageBox.critical(self, "Error", "An unexpected error occurred during login")
        
        finally:
            # Re-enable buttons
            self.login_button.setEnabled(True)
            self.signup_button.setEnabled(True)
            self.cancel_button.setEnabled(True)
            self.login_button.setText("Login")
    
    def show_signup(self):
        """Show signup dialog"""
        from views.signup_dialog import SignupDialog
        
        # Show signup dialog without closing login dialog
        signup_dialog = SignupDialog(self.parent())
        signup_dialog.signup_successful.connect(self.on_signup_successful)
        signup_dialog.exec()
    
    def on_signup_successful(self):
        """Handle successful signup"""
        # Show success message and clear login form
        QMessageBox.information(self, "Account Created", 
                              "Your account has been created successfully!\n\n"
                              "You can now login with your credentials.")
        
        # Clear login form and focus on username field
        self.reset_form()
        self.username_edit.setFocus()
    
    def reset_form(self):
        """Reset the form fields"""
        self.username_edit.clear()
        self.password_edit.clear()
        self.remember_checkbox.setChecked(False)
        self.username_edit.setFocus()
    
    def get_remember_me(self) -> bool:
        """Get remember me checkbox state"""
        return self.remember_checkbox.isChecked()
