from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QComboBox,
                             QLabel, QHeaderView, QMessageBox)
from PyQt6.QtCore import Qt
from database.models import Author
from views.sheikh_student_dialog import SheikhStudentDialog
from controllers.relation_controller import RelationController

class RelationsWidget(QWidget):
    def __init__(self, author_controller):
        super().__init__()
        self.author_controller = author_controller
        self.relation_controller = RelationController()
        self.setup_ui()
        self.load_authors_combo()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # اختيار المؤلف
        select_layout = QHBoxLayout()
        select_layout.addWidget(QLabel("اختر المؤلف:"))
        self.author_combo = QComboBox()
        # self.load_authors_combo()  # Commented out to prevent session binding issues
        self.author_combo.currentIndexChanged.connect(self.load_relations)
        select_layout.addWidget(self.author_combo)
        select_layout.addStretch()

        add_btn = QPushButton("إضافة علاقة شيخ/طالب")
        add_btn.clicked.connect(self.add_relation)
        select_layout.addWidget(add_btn)

        layout.addLayout(select_layout)

        # جدول العلاقات
        self.relations_table = QTableWidget()
        self.relations_table.setColumnCount(3)
        self.relations_table.setHorizontalHeaderLabels(["النوع", "الاسم", "نوع العلاقة"])
        self.relations_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.relations_table)

    def load_authors_combo(self):
        self.author_combo.clear()
        authors = self.author_controller.get_all_authors()
        for author in authors:
            self.author_combo.addItem(author['name'], author['id'])

    def load_relations(self):
        try:
            author_id = self.author_combo.currentData()
            if not author_id:
                return
            
            # Use relation controller to get relations (handles validation internally)
            relations = self.relation_controller.get_author_relations(author_id)
            
            self.relations_table.setRowCount(len(relations))
            for i, relation in enumerate(relations):
                rel_type = relation['relation_type'] or ''
                if relation['type'] == 'sheikh':
                    self.relations_table.setItem(i, 0, QTableWidgetItem("شيخ"))
                    self.relations_table.setItem(i, 1, QTableWidgetItem(relation['name']))
                    self.relations_table.setItem(i, 2, QTableWidgetItem(rel_type))
                else:  # student
                    self.relations_table.setItem(i, 0, QTableWidgetItem("طالب"))
                    self.relations_table.setItem(i, 1, QTableWidgetItem(relation['name']))
                    self.relations_table.setItem(i, 2, QTableWidgetItem(rel_type))
                    
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل العلاقات: {e}")

    def add_relation(self):
        try:
            current_author_id = self.author_combo.currentData()
            if not current_author_id:
                QMessageBox.warning(self, "Warning", "Please select an author first")
                return
            
            # Validate author_id
            try:
                current_author_id = int(current_author_id)
                if current_author_id <= 0:
                    return
            except (ValueError, TypeError):
                return
            
            dialog = SheikhStudentDialog(self.author_controller, current_author_id, self)
            if dialog.exec():
                self.load_relations()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add relation: {e}")
