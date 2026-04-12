import os
import shutil
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QProgressBar, QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import QThread, pyqtSignal
import logging

logger = logging.getLogger(__name__)

class BackupWorker(QThread):
    """Worker thread for database backup operations"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, source_path, backup_path):
        super().__init__()
        self.source_path = source_path
        self.backup_path = backup_path
    
    def run(self):
        try:
            # Ensure backup directory exists
            backup_dir = os.path.dirname(self.backup_path)
            os.makedirs(backup_dir, exist_ok=True)
            
            # Copy database file
            shutil.copy2(self.source_path, self.backup_path)
            
            self.progress.emit(100)
            self.finished.emit(True, f"Backup completed successfully: {self.backup_path}")
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            self.finished.emit(False, f"Backup failed: {e}")

class BackupManager:
    """Utility class for managing database backups"""
    
    @staticmethod
    def create_backup(parent=None, show_progress=True):
        """Create a backup of the database"""
        try:
            # Database file path
            db_path = "tahqiq_data.db"
            if not os.path.exists(db_path):
                QMessageBox.warning(parent, "Backup Error", "Database file not found")
                return False
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"tahqiq_backup_{timestamp}.db"
            
            # Get save file path
            backup_path, _ = QFileDialog.getSaveFileName(
                parent,
                "Create Database Backup",
                default_filename,
                "Database Files (*.db);;All Files (*)"
            )
            
            if not backup_path:
                return False
            
            if show_progress:
                # Show progress dialog
                progress_dialog = BackupProgressDialog(parent, db_path, backup_path)
                return progress_dialog.exec()
            else:
                # Direct backup without progress dialog
                try:
                    backup_dir = os.path.dirname(backup_path)
                    os.makedirs(backup_dir, exist_ok=True)
                    shutil.copy2(db_path, backup_path)
                    QMessageBox.information(parent, "Backup Successful", f"Database backed up to: {backup_path}")
                    return True
                except Exception as e:
                    QMessageBox.critical(parent, "Backup Error", f"Failed to create backup: {e}")
                    return False
                    
        except Exception as e:
            QMessageBox.critical(parent, "Backup Error", f"Backup setup failed: {e}")
            return False
    
    @staticmethod
    def restore_backup(parent=None):
        """Restore database from backup"""
        try:
            # Get backup file path
            backup_path, _ = QFileDialog.getOpenFileName(
                parent,
                "Restore Database Backup",
                "",
                "Database Files (*.db);;All Files (*)"
            )
            
            if not backup_path:
                return False
            
            # Confirm restore operation
            reply = QMessageBox.question(
                parent,
                "Confirm Restore",
                "This will replace the current database with the backup. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return False
            
            # Create backup of current database before restore
            current_db = "tahqiq_data.db"
            if os.path.exists(current_db):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pre_restore_backup = f"tahqiq_prerestore_{timestamp}.db"
                shutil.copy2(current_db, pre_restore_backup)
                logger.info(f"Created pre-restore backup: {pre_restore_backup}")
            
            # Restore from backup
            shutil.copy2(backup_path, current_db)
            
            QMessageBox.information(parent, "Restore Successful", 
                                  f"Database restored from: {backup_path}\n"
                                  f"Previous database backed up as: {pre_restore_backup if os.path.exists(current_db) else 'N/A'}")
            return True
            
        except Exception as e:
            QMessageBox.critical(parent, "Restore Error", f"Failed to restore backup: {e}")
            return False
    
    @staticmethod
    def get_backup_list():
        """Get list of backup files in current directory"""
        try:
            current_dir = Path(".")
            backup_files = []
            
            for file_path in current_dir.glob("tahqiq_backup_*.db"):
                backup_files.append({
                    'name': file_path.name,
                    'path': str(file_path),
                    'size': file_path.stat().st_size,
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime)
                })
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x['modified'], reverse=True)
            return backup_files
            
        except Exception as e:
            logger.error(f"Failed to get backup list: {e}")
            return []

class BackupProgressDialog(QDialog):
    """Dialog showing backup progress"""
    
    def __init__(self, parent, source_path, backup_path):
        super().__init__(parent)
        self.setWindowTitle("Creating Backup...")
        self.setFixedSize(400, 120)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # Status label
        self.status_label = QLabel("Creating database backup...")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.cancel_btn)
        
        # Start backup worker
        self.worker = BackupWorker(source_path, backup_path)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.backup_finished)
        self.worker.start()
    
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
    
    def backup_finished(self, success, message):
        """Handle backup completion"""
        if success:
            self.status_label.setText("Backup completed successfully!")
            QMessageBox.information(self, "Backup Complete", message)
            self.accept()
        else:
            self.status_label.setText("Backup failed!")
            QMessageBox.critical(self, "Backup Failed", message)
            self.reject()
    
    def reject(self):
        """Handle dialog cancellation"""
        if self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
        super().reject()
