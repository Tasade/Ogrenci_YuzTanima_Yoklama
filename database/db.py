# database/db.py
import sqlite3
from datetime import datetime

DB_NAME = "attendance.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Kurs tablosu
    cur.execute("""
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        day TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL
    )
    """)

    # Öğrenci tablosu (yüz verisi dosyalarda tutulacak)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        course_id INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY(course_id) REFERENCES courses(id)
    )
    """)

    # Yoklama tablosu
    cur.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        course_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY(student_id) REFERENCES students(id),
        FOREIGN KEY(course_id) REFERENCES courses(id)
    )
    """)

    conn.commit()

    # 14. Dönem ders programına göre 15 kurs
    courses = [
        ("Proje Uygulaması 1", "Pazartesi", "15:30", "16:30"),
        ("Proje Uygulaması 2", "Pazartesi", "16:45", "17:45"),
        ("Akıllı Tarım Atölyesi", "Pazartesi", "18:00", "19:00"),
        ("Akıllı Trafik Sistemleri Atölyesi", "Pazartesi", "19:15", "20:15"),
        ("Afet ve Güvenlik Tek. Atölyesi", "Pazartesi", "20:30", "21:30"),

        ("Proje Uygulaması 3", "Salı", "15:30", "16:30"),
        ("Proje Uygulaması 4", "Salı", "16:45", "17:45"),
        ("Mbot robotla akıllı rotalar Atölyesi", "Salı", "18:00", "19:00"),
        ("Afet ve Güvenlik Tek. Atölyesi", "Salı", "19:15", "20:15"),
        ("Akıllı Tarım Atölyesi", "Salı", "20:30", "21:30"),

        ("Proje Uygulaması 5", "Çarşamba", "15:30", "16:30"),
        ("Proje Uygulaması 6", "Çarşamba", "16:45", "17:45"),
        ("Yenilenebilir Enerji Atölyesi", "Çarşamba", "18:00", "19:00"),
        ("Python ile Geleceği Kodla Atölyesi", "Çarşamba", "19:15", "20:15"),
        ("Mbot robotla akıllı rotalar Atölyesi", "Çarşamba", "20:30", "21:30"),
    ]

    cur.execute("SELECT COUNT(*) FROM courses")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO courses (name, day, start_time, end_time)
            VALUES (?, ?, ?, ?)
        """, courses)
        conn.commit()

    conn.close()


def get_all_courses():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT id, name, day, start_time, end_time
    FROM courses
    ORDER BY day, start_time
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def add_student(name, course_id):
    """Öğrenciyi kaydeder ve ID'sini döner."""
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.now().isoformat(timespec="seconds")
    cur.execute("""
        INSERT INTO students (name, course_id, created_at)
        VALUES (?, ?, ?)
    """, (name, course_id, now))
    conn.commit()
    student_id = cur.lastrowid
    conn.close()
    return student_id


def get_students_by_course(course_id):
    """(id, name) listesi döner."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name FROM students
        WHERE course_id=?
    """, (course_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_students_ids_by_course(course_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM students WHERE course_id=?", (course_id,))
    ids = [r[0] for r in cur.fetchall()]
    conn.close()
    return ids


def save_attendance(student_id, course_id, status):
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.now()
    d = now.date().isoformat()
    t = now.time().strftime("%H:%M:%S")
    cur.execute("""
        INSERT INTO attendance (student_id, course_id, date, time, status)
        VALUES (?, ?, ?, ?, ?)
    """, (student_id, course_id, d, t, status))
    conn.commit()
    conn.close()


def get_attendance():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT a.id, s.name, c.name, a.date, a.time, a.status
    FROM attendance a
    JOIN students s ON a.student_id = s.id
    JOIN courses c ON a.course_id = c.id
    ORDER BY a.date DESC, a.time DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows
