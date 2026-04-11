from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QComboBox,
                             QLabel, QHeaderView, QMessageBox)
from PyQt6.QtCore import Qt
from database.models import Author
from views.sheikh_student_dialog import SheikhStudentDialog

class RelationsWidget(QWidget):
    def __init__(self, author_controller):
        super().__init__()
        self.controller = author_controller
        self.setup_ui()
        # Don't load authors combo during initialization
        # self.load_authors_combo()  # Commented out to prevent session binding issues

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
        authors = self.controller.get_all_authors()
        for author in authors:
            self.author_combo.addItem(author.name, author.id)

    def load_relations(self):
        try:
            author_id = self.author_combo.currentData()
            if not author_id:
                return
            
            # Validate author_id
            try:
                author_id = int(author_id)
                if author_id <= 0:
                    return
            except (ValueError, TypeError):
                return
            
            session = self.controller.db.get_session()
            try:
                author = session.query(Author).get(author_id)
                if not author:
                    return

                rows = []
                # الشيوخ (من تتلمذ عليهم)
                for rel in author.sheikhs:
                    rows.append(("شيخ", rel.sheikh.name, rel.relation_type or ''))
                # الطلاب (من تتلمذوا عليه)
                for rel in author.students:
                    rows.append(("طالب", rel.student.name, rel.relation_type or ''))

                self.relations_table.setRowCount(len(rows))
                for i, (typ, name, rel_type) in enumerate(rows):
                    self.relations_table.setItem(i, 0, QTableWidgetItem(typ))
                    self.relations_table.setItem(i, 1, QTableWidgetItem(name))
                    self.relations_table.setItem(i, 2, QTableWidgetItem(rel_type))
            finally:
                self.controller.db.close_session()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل تحميل العلاقات: {e}")

    def add_relation(self):
        try:
            current_author_id = self.author_combo.currentData()
            if not current_author_id:
                QMessageBox.warning(self, "تنبيه", "الرجاء اختيار مؤلف أولاً")
                return
            
            # Validate author_id
            try:
                current_author_id = int(current_author_id)
                if current_author_id <= 0:
                    QMessageBox.warning(self, "تنبيه", "معرف المؤلف غير صالح")
                    return
            except (ValueError, TypeError):
                QMessageBox.warning(self, "تنبيه", "معرف المؤلف غير صالح")
                return
            
            dialog = SheikhStudentDialog(self.controller, current_author_id, self)
            if dialog.exec():
                self.load_relations()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل إضافة العلاقة: {e}")
