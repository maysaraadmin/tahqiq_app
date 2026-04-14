from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QHeaderView, 
                             QLabel, QMessageBox, QComboBox, QLineEdit, QGroupBox,
                             QProgressBar, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal
from controllers.investigation_controller import InvestigationController
from controllers.auth_controller import auth_controller
import logging

logger = logging.getLogger(__name__)

class InvestigationListWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.investigation_controller = InvestigationController()
        self.current_user_id = None
        
        self.setup_ui()
        self.load_investigations()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header section
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Book Investigations")
        title_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; }")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # New investigation button
        self.new_btn = QPushButton("New Investigation")
        self.new_btn.clicked.connect(self.parent_window.show_investigation_dialog)
        self.new_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 8px; }")
        header_layout.addWidget(self.new_btn)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_investigations)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Filter section
        filter_group = QGroupBox("Filter Investigations")
        filter_layout = QHBoxLayout(filter_group)
        
        filter_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "in_progress", "completed", "paused"])
        self.status_filter.currentTextChanged.connect(self.load_investigations)
        filter_layout.addWidget(self.status_filter)
        
        filter_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search investigations...")
        self.search_edit.textChanged.connect(self.load_investigations)
        filter_layout.addWidget(self.search_edit)
        
        filter_layout.addStretch()
        layout.addWidget(filter_group)
        
        # Statistics section
        stats_layout = QHBoxLayout()
        
        self.total_label = QLabel("Total: 0")
        self.in_progress_label = QLabel("In Progress: 0")
        self.completed_label = QLabel("Completed: 0")
        
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.in_progress_label)
        stats_layout.addWidget(self.completed_label)
        stats_layout.addStretch()
        
        layout.addLayout(stats_layout)
        
        # Investigations table
        self.investigations_table = QTableWidget()
        self.investigations_table.setColumnCount(8)
        self.investigations_table.setHorizontalHeaderLabels([
            "ID", "Title", "Book", "Status", "Start Date", "Files", "Comparisons", "Actions"
        ])
        self.investigations_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.investigations_table.setSortingEnabled(True)
        self.investigations_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.investigations_table.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.investigations_table)
        
        # Progress bar for loading
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def load_investigations(self):
        """Load investigations for current user"""
        try:
            # Get current user
            current_user = auth_controller.get_current_user()
            if not current_user:
                self.investigations_table.setRowCount(0)
                return
            
            self.current_user_id = current_user.id
            
            # Show progress
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            
            # Get investigations
            investigations = self.investigation_controller.get_user_investigations(self.current_user_id)
            
            # Apply filters
            status_filter = self.status_filter.currentText()
            search_text = self.search_edit.text().lower()
            
            filtered_investigations = []
            for inv in investigations:
                # Status filter
                if status_filter != "All" and inv['status'] != status_filter:
                    continue
                
                # Search filter
                if search_text:
                    if (search_text not in inv['title'].lower() and 
                        search_text not in inv['book_title'].lower() and
                        search_text not in (inv['description'] or '').lower()):
                        continue
                
                filtered_investigations.append(inv)
            
            # Update table
            self.investigations_table.setRowCount(len(filtered_investigations))
            
            for i, inv in enumerate(filtered_investigations):
                self.investigations_table.setItem(i, 0, QTableWidgetItem(str(inv['id'])))
                self.investigations_table.setItem(i, 1, QTableWidgetItem(inv['title']))
                self.investigations_table.setItem(i, 2, QTableWidgetItem(inv['book_title']))
                
                # Status with color coding
                status_item = QTableWidgetItem(inv['status'].replace('_', ' ').title())
                from PyQt6.QtGui import QColor
                if inv['status'] == 'completed':
                    status_item.setForeground(QColor(0, 128, 0))  # Green
                elif inv['status'] == 'in_progress':
                    status_item.setForeground(QColor(0, 0, 255))  # Blue
                elif inv['status'] == 'paused':
                    status_item.setForeground(QColor(255, 165, 0))  # Orange
                
                self.investigations_table.setItem(i, 3, status_item)
                
                # Start date
                start_date = inv['start_date'][:10] if inv['start_date'] else 'N/A'
                self.investigations_table.setItem(i, 4, QTableWidgetItem(start_date))
                
                # Files count
                self.investigations_table.setItem(i, 5, QTableWidgetItem(str(inv['files_count'])))
                
                # Comparisons count
                self.investigations_table.setItem(i, 6, QTableWidgetItem(str(inv['comparisons_count'])))
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                
                # Open button
                open_btn = QPushButton("Open")
                open_btn.clicked.connect(lambda checked, inv_data=inv: self.open_investigation(inv_data))
                open_btn.setMaximumWidth(60)
                actions_layout.addWidget(open_btn)
                
                # Delete button
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(lambda checked, inv_id=inv['id']: self.delete_investigation(inv_id))
                delete_btn.setMaximumWidth(60)
                delete_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
                actions_layout.addWidget(delete_btn)
                
                self.investigations_table.setCellWidget(i, 7, actions_widget)
            
            # Update statistics
            self.update_statistics(investigations)
            
        except Exception as e:
            logger.error(f"Failed to load investigations: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load investigations: {e}")
        finally:
            self.progress_bar.setVisible(False)

    def update_statistics(self, investigations):
        """Update statistics labels"""
        total = len(investigations)
        in_progress = len([inv for inv in investigations if inv['status'] == 'in_progress'])
        completed = len([inv for inv in investigations if inv['status'] == 'completed'])
        
        self.total_label.setText(f"Total: {total}")
        self.in_progress_label.setText(f"In Progress: {in_progress}")
        self.completed_label.setText(f"Completed: {completed}")

    def open_investigation(self, investigation_data):
        """Open investigation dialog"""
        try:
            # Get full investigation details
            details = self.investigation_controller.get_investigation_details(investigation_data['id'])
            
            # Create investigation data for dialog
            inv_data = {
                'book_id': details['book_id'],
                'title': details['title'],
                'description': details['description'],
                'methodology': details['methodology'],
                'objectives': details['objectives'],
                'book_title': details['book_title'],
                'author_name': '',  # This would need to be fetched
                'investigation_id': details['id']  # Add ID for editing
            }
            
            self.parent_window.open_investigation(inv_data)
            
        except Exception as e:
            logger.error(f"Failed to open investigation: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open investigation: {e}")

    def delete_investigation(self, investigation_id):
        """Delete an investigation"""
        reply = QMessageBox.question(
            self, 
            "Confirm Delete",
            "Are you sure you want to delete this investigation and all its data?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            self.investigation_controller.delete_investigation(investigation_id)
            self.load_investigations()
            QMessageBox.information(self, "Success", "Investigation deleted successfully")
            
        except Exception as e:
            logger.error(f"Failed to delete investigation: {e}")
            QMessageBox.critical(self, "Error", f"Failed to delete investigation: {e}")

    def show_context_menu(self, position):
        """Show context menu for investigations table"""
        item = self.investigations_table.itemAt(position)
        if not item:
            return
        
        row = item.row()
        investigation_id = int(self.investigations_table.item(row, 0).text())
        
        menu = QMenu(self)
        
        # Open action
        open_action = menu.addAction("Open Investigation")
        open_action.triggered.connect(lambda: self.open_investigation_by_id(investigation_id))
        
        # View details action
        details_action = menu.addAction("View Details")
        details_action.triggered.connect(lambda: self.view_details(investigation_id))
        
        # Delete action
        delete_action = menu.addAction("Delete Investigation")
        delete_action.triggered.connect(lambda: self.delete_investigation(investigation_id))
        
        menu.exec(self.investigations_table.mapToGlobal(position))

    def open_investigation_by_id(self, investigation_id):
        """Open investigation by ID"""
        try:
            details = self.investigation_controller.get_investigation_details(investigation_id)
            
            inv_data = {
                'book_id': details['book_id'],
                'title': details['title'],
                'description': details['description'],
                'methodology': details['methodology'],
                'objectives': details['objectives'],
                'book_title': details['book_title'],
                'author_name': '',
                'investigation_id': details['id']
            }
            
            self.parent_window.open_investigation(inv_data)
            
        except Exception as e:
            logger.error(f"Failed to open investigation: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open investigation: {e}")

    def view_details(self, investigation_id):
        """View investigation details"""
        try:
            details = self.investigation_controller.get_investigation_details(investigation_id)
            
            details_text = f"Investigation Details:\n\n"
            details_text += f"Title: {details['title']}\n"
            details_text += f"Book: {details['book_title']}\n"
            details_text += f"Status: {details['status']}\n"
            details_text += f"Start Date: {details['start_date'][:10] if details['start_date'] else 'N/A'}\n"
            
            if details['completion_date']:
                details_text += f"Completion Date: {details['completion_date'][:10]}\n"
            
            details_text += f"Files: {len(details['files'])}\n"
            details_text += f"Comparisons: {len(details['comparisons'])}\n\n"
            
            if details['description']:
                details_text += f"Description:\n{details['description']}\n\n"
            
            if details['methodology']:
                details_text += f"Methodology:\n{details['methodology']}\n\n"
            
            if details['objectives']:
                details_text += f"Objectives:\n{details['objectives']}\n\n"
            
            if details['files']:
                details_text += "Uploaded Files:\n"
                for file in details['files']:
                    details_text += f"  - {file['filename']} ({file['file_type']})\n"
                details_text += "\n"
            
            if details['comparisons']:
                details_text += "Comparisons:\n"
                for comp in details['comparisons']:
                    details_text += f"  - {comp['manuscript1_name']} vs {comp['manuscript2_name']}\n"
                    if comp['similarity_score']:
                        details_text += f"    Similarity: {comp['similarity_score']:.2%}\n"
            
            QMessageBox.information(self, "Investigation Details", details_text)
            
        except Exception as e:
            logger.error(f"Failed to view details: {e}")
            QMessageBox.critical(self, "Error", f"Failed to view details: {e}")
