from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, create_engine, Boolean
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from datetime import datetime
import pandas as pd
import os
import glob
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
raw_db_url = os.getenv("DATABASE_URL", "sqlite:///../database/attendance.db")
print(f"[DEBUG] Connected DB: {raw_db_url[:13]}...")

if raw_db_url.startswith("postgres://"):
    DATABASE_URL = raw_db_url.replace("postgres://", "postgresql://", 1)
else:
    DATABASE_URL = raw_db_url
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCEL_PATH = os.path.join(BASE_DIR, "database", "students.xlsx")
TEACHERS_EXCEL_PATH = os.path.join(BASE_DIR, "database", "teachers.xlsx")
STUDENTS_FOLDER = os.path.dirname(EXCEL_PATH)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=2,
        max_overflow=3,
        pool_timeout=30
    )

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Caching Variables
_STUDENT_CACHE = None
_STUDENT_CACHE_TIME = 0
_TEACHER_CACHE = None
_TEACHER_CACHE_TIME = 0

CAMERA_HEARTBEAT_TIMEOUT_SECONDS = 30

SEMESTER_ORDER = [
    "1st Year 1st Semester",
    "1st Year 2nd Semester",
    "2nd Year 1st Semester",
    "2nd Year 2nd Semester",
    "3rd Year 1st Semester",
    "3rd Year 2nd Semester",
    "4th Year 1st Semester",
    "4th Year 2nd Semester",
]


def normalize_semester(text):
    if not text:
        return ""
    return text.strip().lower().replace("semister", "semester").replace("  ", " ")


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    roll_number = Column(String, nullable=True)
    section = Column(String, nullable=True)
    date = Column(String, nullable=False)
    time = Column(String, nullable=False)
    status = Column(String, nullable=False)
    semester = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=True)
    session_id = Column(Integer, ForeignKey('session.id'), nullable=True)

class ClassSession(Base):
    __tablename__ = "class_sessions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, nullable=False)
    section = Column(String, nullable=False)
    first_entry_time = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=True)
    session_id = Column(Integer, ForeignKey('session.id'), nullable=True)

class Session(Base):
    __tablename__ = 'session'
    id = Column(Integer, primary_key=True)
    name = Column(String(20), unique=True, nullable=False)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)

class Course(Base):
    __tablename__ = 'course'
    id = Column(Integer, primary_key=True)
    semester = Column(String(50), nullable=False)
    course_code = Column(String(20), nullable=False)
    course_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

class Enrollment(Base):
    __tablename__ = 'enrollment'
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=False)
    session_id = Column(Integer, ForeignKey('session.id'), nullable=False)
    user_id = Column(String(50), nullable=False)
    name = Column(String(100))
    roll_number = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)

class Camera(Base):
    __tablename__ = 'camera'
    id = Column(Integer, primary_key=True)
    camera_code = Column(String(20), unique=True, nullable=False)
    room_name = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
    current_course_id = Column(Integer, ForeignKey('course.id'), nullable=True)
    current_session_id = Column(Integer, ForeignKey('session.id'), nullable=True)
    # >>> নতুন যোগ করা কলাম (Camera Control ফিচারের জন্য) <<<
    is_enabled = Column(Boolean, default=False, nullable=False)   # admin dashboard থেকে চাওয়া desired state
    last_heartbeat = Column(DateTime, nullable=True)              # camera client শেষ কবে ping করেছে

class CameraCommand(Base):
    __tablename__ = 'camera_command'
    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey('camera.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=False)
    session_id = Column(Integer, ForeignKey('session.id'), nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.now)

class CRAccount(Base):
    __tablename__ = 'cr_account'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('session.id'), nullable=False)
    name = Column(String(100), nullable=False)
    login_email = Column(String(100), unique=True, nullable=False)
    login_password = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

def generate_cr_credentials(session_name):
    dept_code = os.getenv("DEPT_CODE", "dept")
    email = f"cr.{session_name}@{dept_code}.com"
    password = f"cr{session_name.replace('-', '')}"
    return email, password

def get_cr_by_email(email):
    db = SessionLocal()
    try:
        cr = db.query(CRAccount).filter(CRAccount.login_email == email).first()
        if not cr:
            return None
        return {
            "name": cr.name,
            "login_email": cr.login_email,
            "login_password": cr.login_password,
            "session_id": cr.session_id,
            "roll": None,
            "section": None
        }
    finally:
        db.close()

def clean_roll(value):
    s = str(value).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s

def load_students_from_excel():
    global _STUDENT_CACHE, _STUDENT_CACHE_TIME

    pattern = os.path.join(STUDENTS_FOLDER, "students_*.xlsx")
    all_files = glob.glob(pattern)

    if not all_files:
        print(f"[ERROR] কোনো students Excel ফাইল পাওয়া যায়নি")
        return []

    latest_mtime = max(os.path.getmtime(f) for f in all_files)

    if _STUDENT_CACHE is not None and latest_mtime == _STUDENT_CACHE_TIME:
        return _STUDENT_CACHE

    students = []
    seen_rolls = set()

    for file_path in all_files:
        try:
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip().str.lower()
        except Exception as e:
            print(f"[WARNING] {file_path} পড়া যায়নি: {e}")
            continue

        if "session" in df.columns:
            session_col = "session"
        elif "section" in df.columns:
            session_col = "section"
        else:
            session_col = None

        for _, row in df.iterrows():
            roll = clean_roll(row.get("roll", ""))
            if not roll or roll in seen_rolls:
                continue

            session_val = str(row[session_col]).strip() if session_col else ""
            guardian = str(row.get("guardian_email", "")).strip()
            if guardian.lower() == "nan":
                guardian = ""

            students.append({
                "name": str(row.get("name", "")).strip(),
                "roll": roll,
                "section": session_val,
                "login_email": str(row.get("login_email", "")).strip(),
                "login_password": str(row.get("login_password", "")).strip(),
                "guardian_email": guardian,
                "semester": str(row.get("semester", "")).strip()
            })
            seen_rolls.add(roll)
    _STUDENT_CACHE = students
    _STUDENT_CACHE_TIME = latest_mtime
    return students

def load_teachers_from_excel():
    global _TEACHER_CACHE, _TEACHER_CACHE_TIME

    if not os.path.exists(TEACHERS_EXCEL_PATH):
        print(f"[ERROR] {TEACHERS_EXCEL_PATH} পাওয়া যায়নি")
        return []

    current_mtime = os.path.getmtime(TEACHERS_EXCEL_PATH)

    if _TEACHER_CACHE is not None and current_mtime == _TEACHER_CACHE_TIME:
        return _TEACHER_CACHE

    df = pd.read_excel(TEACHERS_EXCEL_PATH)
    df.columns = df.columns.str.strip().str.lower()

    teachers = []
    for _, row in df.iterrows():
        teachers.append({
            "name": str(row["name"]).strip(),
            "designation": str(row.get("designation", "")).strip(),
            "login_email": str(row["login_email"]).strip(),
            "login_password": str(row["login_password"]).strip(),
            "department": str(row.get("department", "")).strip()
        })

    _TEACHER_CACHE = teachers
    _TEACHER_CACHE_TIME = current_mtime
    return teachers

def get_student_by_email(email):
    students = load_students_from_excel()
    for s in students:
        if s["login_email"].lower() == email.lower():
            return s
    return None

def get_student_by_name(name):
    students = load_students_from_excel()
    for s in students:
        if s["name"].lower() == name.lower():
            return s
    return None

def get_teacher_by_email(email):
    teachers = load_teachers_from_excel()
    for t in teachers:
        if t["login_email"].lower() == email.lower():
            return t
    return None

def get_teacher_by_name(name):
    teachers = load_teachers_from_excel()
    for t in teachers:
        if t["name"].lower() == name.lower():
            return t
    return None

def get_batch_semester_map():
    students = load_students_from_excel()
    normalized_semester_to_batch = {}
    for s in students:
        raw_sem = (s.get("semester") or "").strip()
        batch = (s.get("section") or "").strip()
        norm_sem = normalize_semester(raw_sem)
        if norm_sem and batch and norm_sem not in normalized_semester_to_batch:
            normalized_semester_to_batch[norm_sem] = batch
    return normalized_semester_to_batch

def get_admin_from_env():
    return {
        "name": "Admin",
        "login_email": os.getenv("ADMIN_EMAIL", "admin@university.com"),
        "login_password": os.getenv("ADMIN_PASSWORD", "admin123"),
        "role": "admin"
    }

def get_all_cameras_with_status():
    """
    Camera Control page-এর জন্য: সব camera-র সাথে desired state (is_enabled)
    এবং actual live status (heartbeat অনুযায়ী Active/Inactive/Offline) রিটার্ন করে।
    """
    db = SessionLocal()
    try:
        cameras = db.query(Camera).order_by(Camera.camera_code).all()
        result = []
        now = datetime.now()
        for cam in cameras:
            if cam.last_heartbeat is None:
                live_status = "Never Connected"
            else:
                seconds_since = (now - cam.last_heartbeat).total_seconds()
                live_status = "Active" if seconds_since <= CAMERA_HEARTBEAT_TIMEOUT_SECONDS else "Offline"

            result.append({
                "camera_code": cam.camera_code,
                "room_name": cam.room_name,
                "is_enabled": cam.is_enabled,
                "live_status": live_status,
                "last_heartbeat": cam.last_heartbeat.strftime("%Y-%m-%d %H:%M:%S") if cam.last_heartbeat else None,
            })
        return result
    finally:
        db.close()

def set_camera_enabled(camera_code, enabled: bool):
    db = SessionLocal()
    try:
        cam = db.query(Camera).filter(Camera.camera_code == camera_code).first()
        if not cam:
            return False
        cam.is_enabled = enabled
        db.commit()
        return True
    finally:
        db.close()

def set_all_cameras_enabled(enabled: bool):
    db = SessionLocal()
    try:
        db.query(Camera).update({Camera.is_enabled: enabled})
        db.commit()
    finally:
        db.close()

def update_camera_heartbeat(camera_code):
    db = SessionLocal()
    try:
        cam = db.query(Camera).filter(Camera.camera_code == camera_code).first()
        if not cam:
            return False
        cam.last_heartbeat = datetime.now()
        db.commit()
        return True
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
    print("[OK] Database কানেকশন সফল!")

if __name__ == "__main__":
    init_db()