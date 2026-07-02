from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
from datetime import datetime
import pandas as pd
import os
from dotenv import load_dotenv, find_dotenv

# এটি প্রজেক্টের যেকোনো জায়গা থেকে .env ফাইল ঠিকই খুঁজে নেবে
load_dotenv(find_dotenv())

# --- Cloud Database Magic Setup ---
raw_db_url = os.getenv("DATABASE_URL", "sqlite:///../database/attendance.db")

print(f"[DEBUG] Connected DB: {raw_db_url[:13]}...")

if raw_db_url.startswith("postgres://"):
    DATABASE_URL = raw_db_url.replace("postgres://", "postgresql://", 1)
else:
    DATABASE_URL = raw_db_url
    
# EXCEL_PATH = "../database/students.xlsx"
# TEACHERS_EXCEL_PATH = "../database/teachers.xlsx"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCEL_PATH = os.path.join(BASE_DIR, "database", "students.xlsx")
TEACHERS_EXCEL_PATH = os.path.join(BASE_DIR, "database", "teachers.xlsx")

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

# ==========================================
# Caching Variables
# ==========================================
_STUDENT_CACHE = None
_STUDENT_CACHE_TIME = 0

_TEACHER_CACHE = None
_TEACHER_CACHE_TIME = 0


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
    name = Column(String(20), unique=True, nullable=False)  # e.g. "2022-23"
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)
    courses = relationship('Course', backref='session', lazy=True)


class Course(Base):
    __tablename__ = 'course'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('session.id'), nullable=False)
    course_code = Column(String(20), nullable=False)
    course_name = Column(String(100), nullable=False)
    section = Column(String(20))
    created_at = Column(DateTime, default=datetime.now)


class Enrollment(Base):
    __tablename__ = 'enrollment'
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=False)
    user_id = Column(String(50), nullable=False)
    name = Column(String(100))
    roll_number = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)

class Camera(Base):
    __tablename__ = 'camera'
    id = Column(Integer, primary_key=True)
    camera_code = Column(String(20), unique=True, nullable=False)  # "804", "805" ইত্যাদি
    room_name = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)


class CameraCommand(Base):
    __tablename__ = 'camera_command'
    id = Column(Integer, primary_key=True)
    camera_id = Column(Integer, ForeignKey('camera.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('course.id'), nullable=False)
    session_id = Column(Integer, ForeignKey('session.id'), nullable=False)
    status = Column(String(20), default="pending")  # pending / acknowledged
    created_at = Column(DateTime, default=datetime.now)

class CRAccount(Base):
    __tablename__ = 'cr_account'
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('session.id'), nullable=False)
    name = Column(String(100), nullable=False)
    login_email = Column(String(100), unique=True, nullable=False)
    login_password = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

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

def load_students_from_excel():
    global _STUDENT_CACHE, _STUDENT_CACHE_TIME

    if not os.path.exists(EXCEL_PATH):
        print(f"[ERROR] {EXCEL_PATH} পাওয়া যায়নি")
        return []

    # ফাইলের লাস্ট মডিফাই হওয়ার সময় বের করা
    current_mtime = os.path.getmtime(EXCEL_PATH)

    # যদি ক্যাশ থাকে এবং ফাইল পরিবর্তন না হয়ে থাকে, তবে সরাসরি ক্যাশ থেকে রিটার্ন করো (No Pandas needed!)
    if _STUDENT_CACHE is not None and current_mtime == _STUDENT_CACHE_TIME:
        return _STUDENT_CACHE

    # যদি ক্যাশ না থাকে বা নতুন ফাইল আপলোড হয়, কেবল তখনই রিড করো
    df = pd.read_excel(EXCEL_PATH)
    df.columns = df.columns.str.strip().str.lower()

    if "session" in df.columns:
        session_col = "session"
    elif "section" in df.columns:
        session_col = "section"
    else:
        session_col = None

    students = []
    for _, row in df.iterrows():
        session_val = str(row[session_col]).strip() if session_col else ""

        guardian = str(row.get("guardian_email", "")).strip()
        if guardian.lower() == "nan":
            guardian = ""

        students.append({
            "name": str(row["name"]).strip(),
            "roll": str(row["roll"]).strip(),
            "section": session_val,
            "login_email": str(row["login_email"]).strip(),
            "login_password": str(row["login_password"]).strip(),
            "guardian_email": guardian,
            "semester": str(row["semester"]).strip()
        })
    
    # মেমরিতে ডেটা এবং সময় সেভ করে রাখা
    _STUDENT_CACHE = students
    _STUDENT_CACHE_TIME = current_mtime
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


def get_admin_from_env():
    return {
        "name": "Admin",
        "login_email": os.getenv("ADMIN_EMAIL", "admin@university.com"),
        "login_password": os.getenv("ADMIN_PASSWORD", "admin123"),
        "role": "admin"
    }


def init_db():
    Base.metadata.create_all(bind=engine)
    print("[OK] Database কানেকশন সফল!")


if __name__ == "__main__":
    init_db()