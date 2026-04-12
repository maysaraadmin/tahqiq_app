import csv
import os
from datetime import datetime
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import QObject

class CSVExporter(QObject):
    """Utility class for exporting data to CSV files"""
    
    @staticmethod
    def export_authors(authors, parent=None):
        """Export authors list to CSV"""
        try:
            # Get save file path
            file_path, _ = QFileDialog.getSaveFileName(
                parent,
                "Export Authors",
                f"authors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )
            
            if not file_path:
                return False
            
            # Write CSV file
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['ID', 'Name', 'Birth Year', 'Death Year', 'Bio']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for author in authors:
                    writer.writerow({
                        'ID': author['id'],
                        'Name': author['name'],
                        'Birth Year': author.get('birth_year', ''),
                        'Death Year': author.get('death_year', ''),
                        'Bio': author.get('bio', '').replace('\n', ' ') if author.get('bio') else ''
                    })
            
            QMessageBox.information(parent, "Export Successful", f"Authors exported to {file_path}")
            return True
            
        except Exception as e:
            QMessageBox.critical(parent, "Export Error", f"Failed to export authors: {e}")
            return False
    
    @staticmethod
    def export_books(books, parent=None):
        """Export books list to CSV"""
        try:
            # Get save file path
            file_path, _ = QFileDialog.getSaveFileName(
                parent,
                "Export Books",
                f"books_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )
            
            if not file_path:
                return False
            
            # Write CSV file
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['ID', 'Title', 'Author', 'Description', 'Verification Status', 'Studied']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for book in books:
                    writer.writerow({
                        'ID': book['id'],
                        'Title': book['title'],
                        'Author': book['author_name'],
                        'Description': book.get('description', '').replace('\n', ' ') if book.get('description') else '',
                        'Verification Status': book.get('verification_status', 'not_started').replace('_', ' ').title(),
                        'Studied': 'Yes' if book.get('is_studied', False) else 'No'
                    })
            
            QMessageBox.information(parent, "Export Successful", f"Books exported to {file_path}")
            return True
            
        except Exception as e:
            QMessageBox.critical(parent, "Export Error", f"Failed to export books: {e}")
            return False
    
    @staticmethod
    def export_manuscripts(manuscripts, parent=None):
        """Export manuscripts list to CSV"""
        try:
            # Get save file path
            file_path, _ = QFileDialog.getSaveFileName(
                parent,
                "Export Manuscripts",
                f"manuscripts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )
            
            if not file_path:
                return False
            
            # Write CSV file
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['ID', 'Book Title', 'Library Name', 'Shelf Number', 'Copyist', 'Copy Date', 'Notes']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for manuscript in manuscripts:
                    writer.writerow({
                        'ID': manuscript['id'],
                        'Book Title': manuscript['book_title'],
                        'Library Name': manuscript['library_name'],
                        'Shelf Number': manuscript['shelf_number'],
                        'Copyist': manuscript.get('copyist', ''),
                        'Copy Date': manuscript.get('copy_date', ''),
                        'Notes': manuscript.get('notes', '').replace('\n', ' ') if manuscript.get('notes') else ''
                    })
            
            QMessageBox.information(parent, "Export Successful", f"Manuscripts exported to {file_path}")
            return True
            
        except Exception as e:
            QMessageBox.critical(parent, "Export Error", f"Failed to export manuscripts: {e}")
            return False
    
    @staticmethod
    def export_manuscript_index(book_title, manuscripts, parent=None):
        """Export manuscript index for a specific book"""
        try:
            # Get save file path
            safe_title = "".join(c for c in book_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            file_path, _ = QFileDialog.getSaveFileName(
                parent,
                f"Export Manuscript Index - {book_title}",
                f"manuscript_index_{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )
            
            if not file_path:
                return False
            
            # Write CSV file with manuscript index format
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['Book Title', 'Library Name', 'Shelf Number', 'Copyist', 'Copy Date', 'Notes']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for manuscript in manuscripts:
                    writer.writerow({
                        'Book Title': book_title,
                        'Library Name': manuscript['library_name'],
                        'Shelf Number': manuscript['shelf_number'],
                        'Copyist': manuscript.get('copyist', ''),
                        'Copy Date': manuscript.get('copy_date', ''),
                        'Notes': manuscript.get('notes', '').replace('\n', ' ') if manuscript.get('notes') else ''
                    })
            
            QMessageBox.information(parent, "Export Successful", f"Manuscript index exported to {file_path}")
            return True
            
        except Exception as e:
            QMessageBox.critical(parent, "Export Error", f"Failed to export manuscript index: {e}")
            return False
