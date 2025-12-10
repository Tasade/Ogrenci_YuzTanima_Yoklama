# app.py
import subprocess
import sys
import os

# Önce gerekli paketleri kontrol et / kur
try:
    subprocess.run([sys.executable, os.path.join(os.getcwd(), "setup.py")], check=True)
    print("✔ Kütüphane kontrolü tamamlandı.\n")
except Exception as e:
    print("Kurulum sırasında hata:", e)

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QMessageBox, QTableWidget, QTableWidgetItem,
    QHBoxLayout
)

from database.db import (
    init_db, get_all_courses, add_student, get_students_by_course,
    save_attendance, get_attendance, get_students_ids_by_course
)
from face_ai.face_utils import (
    capture_face_samples, run_attendance_for_course
)
from excel.export import export_attendance_to_excel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kurs Merkezli Yüz Tanıma Yoklama Sistemi")
        self.setGeometry(200, 200, 900, 650)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        title = QLabel("Kurs Merkezli Yüz Tanıma Yoklama Sistemi")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        main_layout.addWidget(title)

        # Kurs seçimi
        self.course_combo = QComboBox()
        self.courses = get_all_courses()
        for cid, name, day, st, et in self.courses:
            self.course_combo.addItem(f"{name} | {day} {st}-{et}", cid)

        main_layout.addWidget(QLabel("Kurs Seç:"))
        main_layout.addWidget(self.course_combo)

        # Öğrenci kayıt alanı
        form_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Öğrenci Adı")
        btn_register = QPushButton("Öğrenci Kaydet + Yüz Topla")
        btn_register.clicked.connect(self.register_student)

        form_layout.addWidget(self.name_input)
        form_layout.addWidget(btn_register)
        main_layout.addLayout(form_layout)

        # Yoklama başlat
        btn_attendance = QPushButton("Seçili Kurs İçin Yoklamayı Başlat")
        btn_attendance.clicked.connect(self.start_attendance)
        main_layout.addWidget(btn_attendance)

        # Yoklama tablosu
        self.table = QTableWidget()
        main_layout.addWidget(self.table)

        # Excel'e aktar
        btn_export = QPushButton("Yoklamayı Excel'e Aktar")
        btn_export.clicked.connect(self.export_excel)
        main_layout.addWidget(btn_export)

        self.setCentralWidget(main_widget)
        self.load_attendance_table()

    def get_selected_course(self):
        idx = self.course_combo.currentIndex()
        course_id = self.course_combo.itemData(idx)
        course_name = self.course_combo.currentText()
        return course_id, course_name

    def register_student(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Hata", "Öğrenci adını giriniz.")
            return

        course_id, course_name = self.get_selected_course()

        # Önce DB'ye öğrenci kaydı (id almak için)
        student_id = add_student(name, course_id)

        # Sonra yüz örneklerini topluyoruz
        capture_face_samples(student_id, name, num_samples=30)

        QMessageBox.information(
            self,
            "Başarılı",
            f"'{name}' adlı öğrenci {course_name} kursuna kaydedildi ve yüz örnekleri toplandı."
        )
        self.name_input.clear()

    def start_attendance(self):
        course_id, course_name = self.get_selected_course()
        students = get_students_by_course(course_id)

        if not students:
            QMessageBox.warning(self, "Bilgi", "Bu kurs için kayıtlı öğrenci yok.")
            return

        student_ids = [s[0] for s in students]
        student_names = [s[1] for s in students]

        run_attendance_for_course(
            course_id=course_id,
            course_name=course_name,
            student_ids=student_ids,
            student_names=student_names,
            save_attendance_func=save_attendance,
            mark_absent_after=True,
            get_all_student_ids_func=get_students_ids_by_course
        )

        self.load_attendance_table()
        QMessageBox.information(self, "Bilgi", "Yoklama tamamlandı.")

    def load_attendance_table(self):
        rows = get_attendance()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Öğrenci", "Kurs", "Tarih", "Saat", "Durum"]
        )
        self.table.setRowCount(len(rows))

        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(val)))

        self.table.resizeColumnsToContents()

    def export_excel(self):
        filename = export_attendance_to_excel()
        QMessageBox.information(self, "Excel", f"Yoklama '{filename}' dosyasına aktarıldı.")


if __name__ == "__main__":
    # Eski attendance.db varsa, şema değiştiği için silmek mantıklı
    # ilk çalıştırmadan önce manuel silebilirsin.
    init_db()
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
