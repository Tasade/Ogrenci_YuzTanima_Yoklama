# excel/export.py
import pandas as pd
from database.db import get_attendance


def export_attendance_to_excel(filename="yoklama_kaydi.xlsx"):
    rows = get_attendance()
    df = pd.DataFrame(rows, columns=[
        "ID",
        "Öğrenci",
        "Kurs",
        "Tarih",
        "Saat",
        "Durum"
    ])
    df.to_excel(filename, index=False)
    return filename
