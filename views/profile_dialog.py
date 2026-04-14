from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QFormLayout, QGroupBox, QTextEdit,
    QTabWidget, QWidget, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime
from PyQt6.QtGui import QFont
from controllers.auth_controller import auth_controller
from database.models import User
import logging

logger = logging.getLogger(__name__)

class ProfileDialog(QDialog):
    """Dialog for viewing and editing user profile"""
    
    # Signal emitted when profile is updated
    profile_updated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("User Profile - Tahqiq")
        self.setModal(True)
        self.setFixedSize(500, 600)
        
        # Get current user
        self.current_user = auth_controller.get_current_user()
        
        # Setup UI
        self.setup_ui()
        self.load_user_data()
        
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
        title_label = QLabel("User Profile")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        
        # Profile tab
        self.profile_tab = self.create_profile_tab()
        self.tab_widget.addTab(self.profile_tab, "Profile")
        
        # Security tab
        self.security_tab = self.create_security_tab()
        self.tab_widget.addTab(self.security_tab, "Security")
        
        # Statistics tab
        self.stats_tab = self.create_stats_tab()
        self.tab_widget.addTab(self.stats_tab, "Statistics")
        
        layout.addWidget(self.tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_profile)
        self.save_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        
        self.logout_button = QPushButton("Logout")
        self.logout_button.clicked.connect(self.handle_logout)
        self.logout_button.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.logout_button)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def create_profile_tab(self):
        """Create the profile information tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Basic information group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout()
        
        # Username (read-only)
        self.username_label = QLabel()
        basic_layout.addRow("Username:", self.username_label)
        
        # Full name (editable)
        self.full_name_edit = QLineEdit()
        self.full_name_edit.setPlaceholderText("Enter your full name")
        basic_layout.addRow("Full Name:", self.full_name_edit)
        
        # Email (editable)
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("Enter your email address")
        basic_layout.addRow("Email:", self.email_edit)
        
        # Account status
        self.status_label = QLabel()
        basic_layout.addRow("Account Status:", self.status_label)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # Account information group
        account_group = QGroupBox("Account Information")
        account_layout = QFormLayout()
        
        # Created date
        self.created_label = QLabel()
        account_layout.addRow("Account Created:", self.created_label)
        
        # Last login
        self.last_login_label = QLabel()
        account_layout.addRow("Last Login:", self.last_login_label)
        
        account_group.setLayout(account_layout)
        layout.addWidget(account_group)
        
        # Notes
        notes_label = QLabel("Note: Username cannot be changed after account creation.")
        notes_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(notes_label)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def create_security_tab(self):
        """Create the security settings tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Change password group
        password_group = QGroupBox("Change Password")
        password_layout = QFormLayout()
        
        # Current password
        self.current_password_edit = QLineEdit()
        self.current_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.current_password_edit.setPlaceholderText("Enter current password")
        password_layout.addRow("Current Password:", self.current_password_edit)
        
        # New password
        self.new_password_edit = QLineEdit()
        self.new_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_edit.setPlaceholderText("Enter new password")
        password_layout.addRow("New Password:", self.new_password_edit)
        
        # Confirm new password
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_edit.setPlaceholderText("Confirm new password")
        password_layout.addRow("Confirm New Password:", self.confirm_password_edit)
        
        password_group.setLayout(password_layout)
        layout.addWidget(password_group)
        
        # Change password button
        self.change_password_button = QPushButton("Change Password")
        self.change_password_button.clicked.connect(self.change_password)
        self.change_password_button.setStyleSheet("QPushButton { background-color: #2196F3; color: white; }")
        layout.addWidget(self.change_password_button)
        
        # Password requirements
        requirements_label = QLabel(
            "Password must contain at least 6 characters, including letters and numbers"
        )
        requirements_label.setWordWrap(True)
        requirements_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(requirements_label)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def create_stats_tab(self):
        """Create the statistics tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # User statistics group
        stats_group = QGroupBox("Your Statistics")
        stats_layout = QGridLayout()
        
        # Study sessions
        self.study_sessions_label = QLabel("0")
        stats_layout.addWidget(QLabel("Total Study Sessions:"), 0, 0)
        stats_layout.addWidget(self.study_sessions_label, 0, 1)
        
        # Books studied
        self.books_studied_label = QLabel("0")
        stats_layout.addWidget(QLabel("Books Studied:"), 1, 0)
        stats_layout.addWidget(self.books_studied_label, 1, 1)
        
        # Total study time
        self.total_time_label = QLabel("0 hours")
        stats_layout.addWidget(QLabel("Total Study Time:"), 2, 0)
        stats_layout.addWidget(self.total_time_label, 2, 1)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Activity summary
        activity_group = QGroupBox("Recent Activity")
        activity_layout = QVBoxLayout()
        
        self.activity_text = QTextEdit()
        self.activity_text.setReadOnly(True)
        self.activity_text.setMaximumHeight(150)
        self.activity_text.setPlaceholderText("No recent activity")
        activity_layout.addWidget(self.activity_text)
        
        activity_group.setLayout(activity_layout)
        layout.addWidget(activity_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def load_user_data(self):
        """Load current user data into the form"""
        if not self.current_user:
            return
        
        # Basic information
        self.username_label.setText(self.current_user.username)
        self.full_name_edit.setText(self.current_user.full_name or "")
        self.email_edit.setText(self.current_user.email)
        
        # Account status
        status = "Active" if self.current_user.is_active else "Inactive"
        self.status_label.setText(status)
        self.status_label.setStyleSheet(
            "color: green;" if self.current_user.is_active else "color: red;"
        )
        
        # Account information
        if self.current_user.created_at:
            created_date = self.current_user.created_at.strftime("%Y-%m-%d %H:%M")
            self.created_label.setText(created_date)
        
        if self.current_user.last_login:
            login_date = self.current_user.last_login.strftime("%Y-%m-%d %H:%M")
            self.last_login_label.setText(login_date)
        else:
            self.last_login_label.setText("Never")
        
        # Load statistics
        self.load_statistics()
    
    def load_statistics(self):
        """Load user statistics"""
        if not self.current_user:
            return
        
        try:
            from database.db_manager import DatabaseManager
            from database.models import StudySession
            from sqlalchemy import func
            
            db_manager = DatabaseManager()
            session = db_manager.get_session()
            
            try:
                # Count study sessions
                session_count = session.query(StudySession).filter(
                    StudySession.user_id == self.current_user.id
                ).count()
                self.study_sessions_label.setText(str(session_count))
                
                # Count unique books studied
                books_count = session.query(StudySession.book_id).filter(
                    StudySession.user_id == self.current_user.id
                ).distinct().count()
                self.books_studied_label.setText(str(books_count))
                
                # Calculate total study time
                total_minutes = session.query(func.sum(StudySession.duration_minutes)).filter(
                    StudySession.user_id == self.current_user.id
                ).scalar() or 0
                
                hours = total_minutes // 60
                minutes = total_minutes % 60
                if hours > 0:
                    self.total_time_label.setText(f"{hours}h {minutes}m")
                else:
                    self.total_time_label.setText(f"{minutes} minutes")
                
                # Recent activity
                recent_sessions = session.query(StudySession).filter(
                    StudySession.user_id == self.current_user.id
                ).order_by(StudySession.session_date.desc()).limit(5).all()
                
                if recent_sessions:
                    activity_text = "Recent study sessions:\n\n"
                    for session in recent_sessions:
                        date_str = session.session_date.strftime("%Y-%m-%d %H:%M")
                        activity_text += f"  {date_str} - {session.duration_minutes} minutes\n"
                        if session.notes:
                            activity_text += f"    Notes: {session.notes[:50]}...\n"
                        activity_text += "\n"
                    
                    self.activity_text.setText(activity_text)
                else:
                    self.activity_text.setText("No study sessions recorded yet.")
                
            finally:
                db_manager.close_session(session)
                
        except Exception as e:
            logger.error(f"Error loading user statistics: {e}")
            self.activity_text.setText("Error loading statistics")
    
    def save_profile(self):
        """Save profile changes"""
        if not self.current_user:
            return
        
        # Get form data
        full_name = self.full_name_edit.text().strip() or None
        email = self.email_edit.text().strip()
        
        # Validate email
        if not email:
            QMessageBox.warning(self, "Validation Error", "Email is required")
            self.tab_widget.setCurrentIndex(0)  # Switch to profile tab
            self.email_edit.setFocus()
            return
        
        # Save changes
        try:
            success, message = auth_controller.update_profile(
                self.current_user.id, full_name, email
            )
            
            if success:
                QMessageBox.information(self, "Success", message)
                self.profile_updated.emit()
                # Reload user data
                self.current_user = auth_controller.get_current_user()
                self.load_user_data()
            else:
                QMessageBox.warning(self, "Update Failed", message)
        
        except Exception as e:
            logger.error(f"Save profile error: {e}")
            QMessageBox.critical(self, "Error", "An unexpected error occurred")
    
    def change_password(self):
        """Change user password"""
        current_password = self.current_password_edit.text()
        new_password = self.new_password_edit.text()
        confirm_password = self.confirm_password_edit.text()
        
        # Validate inputs
        if not current_password or not new_password or not confirm_password:
            QMessageBox.warning(self, "Validation Error", 
                               "All password fields are required")
            return
        
        if new_password != confirm_password:
            QMessageBox.warning(self, "Validation Error", 
                               "New passwords do not match")
            return
        
        # Change password
        try:
            success, message = auth_controller.change_password(
                self.current_user.id, current_password, new_password
            )
            
            if success:
                QMessageBox.information(self, "Success", message)
                # Clear password fields
                self.current_password_edit.clear()
                self.new_password_edit.clear()
                self.confirm_password_edit.clear()
            else:
                QMessageBox.warning(self, "Password Change Failed", message)
        
        except Exception as e:
            logger.error(f"Change password error: {e}")
            QMessageBox.critical(self, "Error", "An unexpected error occurred")
    
    def handle_logout(self):
        """Handle logout button click"""
        reply = QMessageBox.question(
            self, "Confirm Logout", 
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                success, message = auth_controller.logout()
                if success:
                    QMessageBox.information(self, "Success", message)
                    self.accept()  # Close profile dialog
                else:
                    QMessageBox.warning(self, "Logout Failed", message)
            except Exception as e:
                logger.error(f"Logout error: {e}")
                QMessageBox.critical(self, "Error", "An unexpected error occurred")
