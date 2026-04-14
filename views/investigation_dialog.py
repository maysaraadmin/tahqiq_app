from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QFormLayout, QMessageBox,
                             QTabWidget, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QFileDialog, QProgressBar, QGroupBox,
                             QSplitter, QScrollArea, QComboBox, QLineEdit, QWidget,
                             QInputDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from controllers.investigation_controller import InvestigationController
from controllers.comparison_controller import ComparisonController
from controllers.manuscript_controller import ManuscriptController
import os
import logging

logger = logging.getLogger(__name__)

class FileUploadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str, str)  # file_path, message
    error = pyqtSignal(str)

    def __init__(self, temp_file_path, original_filename, investigation_id, description=None, manuscript_id=None):
        super().__init__()
        self.temp_file_path = temp_file_path
        self.original_filename = original_filename
        self.investigation_id = investigation_id
        self.description = description
        self.manuscript_id = manuscript_id
        self.investigation_controller = InvestigationController()

    def run(self):
        try:
            self.progress.emit(10)
            
            # Upload file
            file_id = self.investigation_controller.upload_file(
                self.investigation_id,
                self.temp_file_path,
                self.original_filename,
                self.description,
                self.manuscript_id
            )
            
            self.progress.emit(90)
            
            # Clean up temp file
            try:
                os.remove(self.temp_file_path)
            except:
                pass
            
            self.progress.emit(100)
            self.finished.emit(str(file_id), f"Successfully uploaded: {self.original_filename}")
            
        except Exception as e:
            self.error.emit(str(e))

class InvestigationDialog(QDialog):
    def __init__(self, investigation_data, parent=None):
        super().__init__(parent)
        self.investigation_data = investigation_data
        self.investigation_controller = InvestigationController()
        self.comparison_controller = ComparisonController()
        self.manuscript_controller = ManuscriptController()
        
        self.investigation_id = None
        self.current_user_id = None  # This should be set from auth controller
        
        self.setWindowTitle(f"Investigation: {investigation_data.get('title', 'New Investigation')}")
        self.setMinimumWidth(1200)
        self.setMinimumHeight(800)
        
        self.setup_ui()
        self.create_investigation()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - Investigation details and files
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Investigation details
        details_group = QGroupBox("Investigation Details")
        details_layout = QFormLayout(details_group)
        
        self.title_label = QLabel(self.investigation_data.get('title', ''))
        details_layout.addRow("Title:", self.title_label)
        
        self.book_label = QLabel(self.investigation_data.get('book_title', ''))
        details_layout.addRow("Book:", self.book_label)
        
        self.author_label = QLabel(self.investigation_data.get('author_name', ''))
        details_layout.addRow("Author:", self.author_label)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlainText(self.investigation_data.get('description', ''))
        self.description_edit.setMaximumHeight(100)
        details_layout.addRow("Description:", self.description_edit)
        
        self.methodology_edit = QTextEdit()
        self.methodology_edit.setPlainText(self.investigation_data.get('methodology', ''))
        self.methodology_edit.setMaximumHeight(80)
        details_layout.addRow("Methodology:", self.methodology_edit)
        
        self.objectives_edit = QTextEdit()
        self.objectives_edit.setPlainText(self.investigation_data.get('objectives', ''))
        self.objectives_edit.setMaximumHeight(80)
        details_layout.addRow("Objectives:", self.objectives_edit)
        
        left_layout.addWidget(details_group)
        
        # File upload section
        upload_group = QGroupBox("Upload Files")
        upload_layout = QVBoxLayout(upload_group)
        
        # Upload controls
        upload_controls = QHBoxLayout()
        
        self.upload_btn = QPushButton("Upload File (PDF/Word)")
        self.upload_btn.clicked.connect(self.upload_file)
        upload_controls.addWidget(self.upload_btn)
        
        self.upload_progress = QProgressBar()
        self.upload_progress.setVisible(False)
        upload_controls.addWidget(self.upload_progress)
        
        upload_layout.addLayout(upload_controls)
        
        # Manuscript linking
        manuscript_layout = QHBoxLayout()
        manuscript_layout.addWidget(QLabel("Link to Manuscript:"))
        
        self.manuscript_combo = QComboBox()
        manuscript_layout.addWidget(self.manuscript_combo)
        
        upload_layout.addLayout(manuscript_layout)
        
        # Files table
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(5)
        self.files_table.setHorizontalHeaderLabels(["Filename", "Type", "Size", "Date", "Actions"])
        self.files_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        upload_layout.addWidget(self.files_table)
        
        left_layout.addWidget(upload_group)
        
        # Comparisons section
        comparison_group = QGroupBox("Manuscript Comparisons")
        comparison_layout = QVBoxLayout(comparison_group)
        
        # Comparison controls
        comparison_controls = QHBoxLayout()
        
        self.compare_btn = QPushButton("Compare Selected Manuscripts")
        self.compare_btn.clicked.connect(self.compare_manuscripts)
        self.compare_btn.setEnabled(False)
        comparison_controls.addWidget(self.compare_btn)
        
        comparison_controls.addStretch()
        comparison_layout.addLayout(comparison_controls)
        
        # Comparisons table
        self.comparisons_table = QTableWidget()
        self.comparisons_table.setColumnCount(6)
        self.comparisons_table.setHorizontalHeaderLabels(["Manuscript 1", "Manuscript 2", "Similarity", "Differences", "Date", "Actions"])
        self.comparisons_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        comparison_layout.addWidget(self.comparisons_table)
        
        left_layout.addWidget(comparison_group)
        
        # Right panel - Analysis and results
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Create tab widget for different views
        self.tab_widget = QTabWidget()
        
        # Results tab
        results_widget = QWidget()
        results_layout = QVBoxLayout(results_widget)
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setPlainText("Analysis results will appear here...")
        results_layout.addWidget(self.results_text)
        
        self.tab_widget.addTab(results_widget, "Analysis Results")
        
        # Details tab
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setPlainText("Detailed comparison results will appear here...")
        details_layout.addWidget(self.details_text)
        
        self.tab_widget.addTab(details_widget, "Detailed Analysis")
        
        right_layout.addWidget(self.tab_widget)
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 600])
        
        layout.addWidget(splitter)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save Investigation")
        self.save_btn.clicked.connect(self.save_investigation)
        
        self.complete_btn = QPushButton("Mark Complete")
        self.complete_btn.clicked.connect(self.complete_investigation)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.complete_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)

    def create_investigation(self):
        """Create the investigation in database"""
        try:
            # Get current user ID (this should come from auth controller)
            from controllers.auth_controller import auth_controller
            current_user = auth_controller.get_current_user()
            if not current_user:
                QMessageBox.critical(self, "Error", "User not authenticated")
                self.reject()
                return
            
            self.current_user_id = current_user.id
            
            # Create investigation
            self.investigation_id = self.investigation_controller.create_investigation(
                book_id=self.investigation_data['book_id'],
                user_id=self.current_user_id,
                title=self.investigation_data.get('title'),
                description=self.investigation_data.get('description'),
                methodology=self.investigation_data.get('methodology'),
                objectives=self.investigation_data.get('objectives')
            )
            
            # Load manuscripts for this book
            self.load_manuscripts()
            self.load_files()
            self.load_comparisons()
            
            logger.info(f"Created investigation: {self.investigation_id}")
            
        except Exception as e:
            logger.error(f"Failed to create investigation: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create investigation: {e}")

    def load_manuscripts(self):
        """Load manuscripts for the book"""
        try:
            manuscripts = self.manuscript_controller.get_book_manuscripts(self.investigation_data['book_id'])
            
            self.manuscript_combo.clear()
            self.manuscript_combo.addItem("No manuscript linked", None)
            
            for manuscript in manuscripts:
                display_text = f"{manuscript['library_name']} - {manuscript['shelf_number']}"
                self.manuscript_combo.addItem(display_text, manuscript['id'])
            
        except Exception as e:
            logger.error(f"Failed to load manuscripts: {e}")

    def load_files(self):
        """Load uploaded files"""
        if not self.investigation_id:
            return
        
        try:
            files = self.investigation_controller.get_investigation_files(self.investigation_id)
            
            self.files_table.setRowCount(len(files))
            
            for i, file in enumerate(files):
                self.files_table.setItem(i, 0, QTableWidgetItem(file['filename']))
                self.files_table.setItem(i, 1, QTableWidgetItem(file['file_type']))
                self.files_table.setItem(i, 2, QTableWidgetItem(f"{file['file_size']:,} bytes"))
                self.files_table.setItem(i, 3, QTableWidgetItem(file['upload_date'][:10]))
                
                # Add action buttons
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                
                # Open button
                open_btn = QPushButton("Open")
                open_btn.clicked.connect(lambda checked, file_path=file['file_path'], filename=file['filename']: self.open_file(file_path, filename))
                open_btn.setMaximumWidth(60)
                actions_layout.addWidget(open_btn)
                
                # Delete button
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(lambda checked, file_id=file['id']: self.delete_file(file_id))
                delete_btn.setMaximumWidth(60)
                delete_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
                actions_layout.addWidget(delete_btn)
                
                self.files_table.setCellWidget(i, 4, actions_widget)
            
        except Exception as e:
            logger.error(f"Failed to load files: {e}")

    def load_comparisons(self):
        """Load manuscript comparisons"""
        if not self.investigation_id:
            return
        
        try:
            comparisons = self.comparison_controller.get_investigation_comparisons(self.investigation_id)
            
            self.comparisons_table.setRowCount(len(comparisons))
            
            for i, comp in enumerate(comparisons):
                self.comparisons_table.setItem(i, 0, QTableWidgetItem(comp['manuscript1_name']))
                self.comparisons_table.setItem(i, 1, QTableWidgetItem(comp['manuscript2_name']))
                
                similarity_text = f"{comp['similarity_score']:.2%}" if comp['similarity_score'] else "Pending"
                self.comparisons_table.setItem(i, 2, QTableWidgetItem(similarity_text))
                
                self.comparisons_table.setItem(i, 3, QTableWidgetItem(str(comp['differences_count'])))
                self.comparisons_table.setItem(i, 4, QTableWidgetItem(comp['comparison_date'][:10]))
                
                # Add view button
                view_btn = QPushButton("View Details")
                view_btn.clicked.connect(lambda checked, comp_id=comp['id']: self.view_comparison(comp_id))
                self.comparisons_table.setCellWidget(i, 5, view_btn)
            
            # Enable compare button if we have manuscripts
            self.compare_btn.setEnabled(len(comparisons) > 0)
            
        except Exception as e:
            logger.error(f"Failed to load comparisons: {e}")

    def upload_file(self):
        """Upload a file to the investigation"""
        if not self.investigation_id:
            QMessageBox.warning(self, "Warning", "Investigation not created yet")
            return
        
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Upload",
            "",
            "PDF Files (*.pdf);;Word Documents (*.docx *.doc);;Text Files (*.txt);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # Get manuscript selection
        manuscript_id = self.manuscript_combo.currentData()
        
        # Get file description
        description, ok = QInputDialog.getText(self, "File Description", "Enter file description (optional):")
        if not ok:
            return
        
        # Create temporary copy for upload
        import tempfile
        temp_dir = tempfile.gettempdir()
        temp_file_path = os.path.join(temp_dir, os.path.basename(file_path))
        
        try:
            import shutil
            shutil.copy2(file_path, temp_file_path)
            
            # Start upload thread
            self.upload_thread = FileUploadThread(
                temp_file_path,
                os.path.basename(file_path),
                self.investigation_id,
                description if description else None,
                manuscript_id if manuscript_id else None
            )
            
            self.upload_thread.progress.connect(self.on_upload_progress)
            self.upload_thread.finished.connect(self.on_upload_finished)
            self.upload_thread.error.connect(self.on_upload_error)
            
            self.upload_btn.setEnabled(False)
            self.upload_progress.setVisible(True)
            self.upload_progress.setValue(0)
            
            self.upload_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to prepare file upload: {e}")
            QMessageBox.critical(self, "Error", f"Failed to prepare file upload: {e}")

    def on_upload_progress(self, value):
        """Handle upload progress"""
        self.upload_progress.setValue(value)

    def on_upload_finished(self, file_id, message):
        """Handle successful upload"""
        self.upload_btn.setEnabled(True)
        self.upload_progress.setVisible(False)
        
        QMessageBox.information(self, "Success", message)
        self.load_files()

    def on_upload_error(self, error_message):
        """Handle upload error"""
        self.upload_btn.setEnabled(True)
        self.upload_progress.setVisible(False)
        
        QMessageBox.critical(self, "Upload Error", error_message)

    def delete_file(self, file_id):
        """Delete a file"""
        reply = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this file?")
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            self.investigation_controller.delete_file(file_id)
            self.load_files()
            QMessageBox.information(self, "Success", "File deleted successfully")
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            QMessageBox.critical(self, "Error", f"Failed to delete file: {e}")

    def compare_manuscripts(self):
        """Compare two manuscripts"""
        # For now, create a sample comparison
        # In real implementation, would show manuscript selection dialog
        QMessageBox.information(self, "Coming Soon", "Manuscript comparison interface will be implemented in the next phase")

    def view_comparison(self, comparison_id):
        """View detailed comparison results"""
        try:
            details = self.comparison_controller.get_comparison_details(comparison_id)
            
            # Display results in the text areas
            results_text = f"Comparison Results:\n\n"
            results_text += f"Manuscript 1: {details['manuscript1_name']}\n"
            results_text += f"Manuscript 2: {details['manuscript2_name']}\n"
            results_text += f"Similarity Score: {details['similarity_score']:.2%}\n"
            results_text += f"Total Differences: {details['differences_count']}\n"
            results_text += f"Total Similarities: {details['similarities_count']}\n"
            results_text += f"Total Words: {details['total_words']:,}\n\n"
            results_text += f"Key Differences:\n{details['key_differences']}\n\n"
            results_text += f"Key Similarities:\n{details['key_similarities']}"
            
            self.results_text.setPlainText(results_text)
            
            # Show detailed analysis
            detailed_text = "Detailed Analysis:\n\n"
            for detail in details['details'][:20]:  # Show first 20 details
                detailed_text += f"Type: {detail['type']}\n"
                if detail['manuscript1_text']:
                    detailed_text += f"Manuscript 1: {detail['manuscript1_text']}\n"
                if detail['manuscript2_text']:
                    detailed_text += f"Manuscript 2: {detail['manuscript2_text']}\n"
                detailed_text += f"Confidence: {detail['confidence_score']:.2%}\n"
                detailed_text += f"Notes: {detail['notes']}\n"
                detailed_text += "-" * 50 + "\n"
            
            self.details_text.setPlainText(detailed_text)
            
            # Switch to results tab
            self.tab_widget.setCurrentIndex(0)
            
        except Exception as e:
            logger.error(f"Failed to view comparison: {e}")
            QMessageBox.critical(self, "Error", f"Failed to view comparison: {e}")

    def save_investigation(self):
        """Save investigation details"""
        if not self.investigation_id:
            return
        
        try:
            self.investigation_controller.update_investigation(
                self.investigation_id,
                description=self.description_edit.toPlainText().strip(),
                methodology=self.methodology_edit.toPlainText().strip(),
                objectives=self.objectives_edit.toPlainText().strip()
            )
            
            QMessageBox.information(self, "Success", "Investigation saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save investigation: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save investigation: {e}")

    def complete_investigation(self):
        """Mark investigation as complete"""
        if not self.investigation_id:
            return
        
        reply = QMessageBox.question(self, "Complete Investigation", 
                                    "Are you sure you want to mark this investigation as complete?")
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            self.investigation_controller.update_investigation(
                self.investigation_id,
                status='completed'
            )
            
            QMessageBox.information(self, "Success", "Investigation marked as complete")
            self.complete_btn.setEnabled(False)
            
        except Exception as e:
            logger.error(f"Failed to complete investigation: {e}")
            QMessageBox.critical(self, "Error", f"Failed to complete investigation: {e}")

    def open_file(self, file_path, filename):
        """Open and read uploaded file"""
        try:
            import subprocess
            import platform
            
            # Check if file exists
            if not os.path.exists(file_path):
                QMessageBox.critical(self, "Error", f"File not found: {file_path}")
                return
            
            # Get file extension
            file_ext = os.path.splitext(filename)[1].lower()
            
            # Handle different file types
            if file_ext == '.pdf':
                self.open_pdf_file(file_path, filename)
            elif file_ext in ['.docx', '.doc']:
                self.open_word_file(file_path, filename)
            elif file_ext == '.txt':
                self.open_text_file(file_path, filename)
            else:
                # Try to open with default system application
                try:
                    if platform.system() == 'Windows':
                        os.startfile(file_path)
                    elif platform.system() == 'Darwin':  # macOS
                        subprocess.run(['open', file_path])
                    else:  # Linux
                        subprocess.run(['xdg-open', file_path])
                except Exception as e:
                    logger.error(f"Failed to open file with system default: {e}")
                    QMessageBox.critical(self, "Error", f"Failed to open file: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to open file: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open file: {e}")

    def open_pdf_file(self, file_path, filename):
        """Open PDF file with system default viewer"""
        try:
            import subprocess
            import platform
            
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', file_path])
            else:  # Linux
                subprocess.run(['xdg-open', file_path])
                
            logger.info(f"Opened PDF file: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to open PDF file: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open PDF file: {e}")

    def open_word_file(self, file_path, filename):
        """Open Word document with system default viewer"""
        try:
            import subprocess
            import platform
            
            if platform.system() == 'Windows':
                # Try to open with Microsoft Word or default application
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', file_path])
            else:  # Linux
                subprocess.run(['xdg-open', file_path])
                
            logger.info(f"Opened Word file: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to open Word file: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open Word file: {e}")

    def open_text_file(self, file_path, filename):
        """Open text file in a dialog"""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create dialog to show content
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Text File: {filename}")
            dialog.setMinimumSize(800, 600)
            
            layout = QVBoxLayout(dialog)
            
            # Text area
            text_edit = QTextEdit()
            text_edit.setPlainText(content)
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)
            
            # Close button
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            layout.addWidget(close_btn)
            
            dialog.exec()
            
            logger.info(f"Opened text file: {filename}")
            
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                
                QMessageBox.information(self, "File Content", f"File content (partial preview):\n\n{content[:1000]}...")
                
            except Exception as e:
                logger.error(f"Failed to read text file with any encoding: {e}")
                QMessageBox.critical(self, "Error", f"Failed to read text file: {e}")
                
        except Exception as e:
            logger.error(f"Failed to open text file: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open text file: {e}")
