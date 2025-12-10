# face_ai/face_utils.py
import cv2
import numpy as np
import os

# Yüz verilerinin tutulacağı klasör
DATA_DIR = "face_data"


def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def capture_face_samples(student_id, student_name, num_samples=30):
    """
    Öğrenci kaydederken, kameradan bu öğrencinin yüzünden num_samples kadar örnek alır.
    Kaydedilen dosya adları: face_data/user.<id>.<num>.jpg
    """
    ensure_data_dir()

    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    count = 0
    print(f"📷 {student_name} için yüz örnekleri toplanıyor...")
    print("Yüzünüzü kameraya gösterin. Çıkmak için 'q'.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            # Yüz bölgesini al
            face_img = gray[y:y+h, x:x+w]
            face_img = cv2.resize(face_img, (200, 200))

            count += 1
            file_name = os.path.join(DATA_DIR, f"user.{student_id}.{count}.jpg")
            cv2.imwrite(file_name, face_img)

            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, f"Kaydedildi: {count}", (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow(f"Yuz Kaydi - {student_name}", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        if count >= num_samples:
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"✔ {student_name} için {count} adet yüz örneği kaydedildi.")


def get_images_and_labels(student_ids):
    """
    face_data klasöründeki resimleri okuyup
    sadece verilen student_ids için (faces, labels) döner.
    """
    ensure_data_dir()
    image_paths = [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR)
                   if f.endswith(".jpg") or f.endswith(".png")]

    face_samples = []
    ids = []

    student_ids_set = set(student_ids)

    for imagePath in image_paths:
        file_name = os.path.basename(imagePath)
        # user.<id>.<num>.jpg
        try:
            parts = file_name.split(".")
            sid = int(parts[1])
        except Exception:
            continue

        if sid not in student_ids_set:
            continue

        img = cv2.imread(imagePath, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue

        face_samples.append(img)
        ids.append(sid)

    if len(face_samples) == 0:
        return None, None

    return face_samples, np.array(ids)


def train_recognizer_for_students(student_ids):
    faces, labels = get_images_and_labels(student_ids)
    if faces is None or len(faces) == 0:
        return None

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(faces, labels)
    return recognizer


def run_attendance_for_course(
    course_id,
    course_name,
    student_ids,
    student_names,
    save_attendance_func,
    mark_absent_after=True,
    get_all_student_ids_func=None
):
    """
    Verilen kurs için:
    - Önce sadece o kursun öğrencilerinden model eğitilir
    - Kamera açılır, tanınan öğrenciler için 'GELDİ' kaydı alınır
    - Çıkışta gelmeyenler 'GELMEDİ' yapılır
    """
    if not student_ids:
        print("Bu kurs için kayıtlı öğrenci yok.")
        return

    recognizer = train_recognizer_for_students(student_ids)
    if recognizer is None:
        print("Bu kurs için yeterli yüz verisi yok. Önce kayıt yapın.")
        return

    id_to_name = {sid: name for sid, name in zip(student_ids, student_names)}
    present_ids = set()

    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    print(f"📌 Yoklama başladı: {course_name} (q ile çık)")
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            face_img = gray[y:y+h, x:x+w]
            face_img = cv2.resize(face_img, (200, 200))

            label, confidence = recognizer.predict(face_img)
            # confidence değeri ne kadar düşükse o kadar iyi
            if confidence < 80 and label in id_to_name:
                name = id_to_name[label]
                sid = label

                if sid not in present_ids:
                    present_ids.add(sid)
                    save_attendance_func(sid, course_id, "GELDİ")

                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, f"{name} (GELDİ)", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            else:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                cv2.putText(frame, "Bilinmiyor", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        cv2.putText(frame, course_name, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

        cv2.imshow("Yoklama", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if mark_absent_after and get_all_student_ids_func is not None:
        all_ids = set(get_all_student_ids_func(course_id))
        for sid in all_ids:
            if sid not in present_ids:
                save_attendance_func(sid, course_id, "GELMEDİ")

    print("✔ Yoklama tamamlandı.")
