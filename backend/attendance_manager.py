from database import SessionLocal, Attendance, ClassSession, get_student_by_name
from datetime import datetime
import pytz

LATE_THRESHOLD_MINUTES = 20

def is_duplicate(roll_number, date, course_id=None):
    db = SessionLocal()
    query = db.query(Attendance).filter(
        Attendance.roll_number == roll_number,
        Attendance.date == date
    )
    if course_id is not None:
        query = query.filter(Attendance.course_id == course_id)
    else:
        query = query.filter(Attendance.course_id.is_(None))

    existing = query.first()
    db.close()
    return existing is not None


def get_or_create_session(date, section):
    db = SessionLocal()
    session = db.query(ClassSession).filter(
        ClassSession.date == date,
        ClassSession.section == section
    ).first()

    if not session:
        session = ClassSession(
            date=date,
            section=section,
            first_entry_time=None
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    db.close()
    return session


def update_first_entry(date, section, time_str):
    db = SessionLocal()
    session = db.query(ClassSession).filter(
        ClassSession.date == date,
        ClassSession.section == section
    ).first()

    if session and session.first_entry_time is None:
        session.first_entry_time = time_str
        db.commit()

    db.close()


def calculate_status(role, section, date, current_time_str):
    if role == "teacher":
        return "Present"

    session = get_or_create_session(date, section)

    if session.first_entry_time is None:
        update_first_entry(date, section, current_time_str)
        return "On Time"

    fmt = "%H:%M:%S"
    first_time = datetime.strptime(session.first_entry_time, fmt)
    current_time = datetime.strptime(current_time_str, fmt)
    diff_minutes = (current_time - first_time).total_seconds() / 60

    return "On Time" if diff_minutes <= LATE_THRESHOLD_MINUTES else "Late"


def mark_attendance(name, role, section=None, semester=None, course_id=None, session_id=None):
    # --- ম্যাজিক কোড শুরু ---
    tz_dhaka = pytz.timezone('Asia/Dhaka')
    now = datetime.now(tz_dhaka)
    # --- ম্যাজিক কোড শেষ ---
    
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    student = get_student_by_name(name)

    from database import get_teacher_by_name

    student = get_student_by_name(name)
    teacher = get_teacher_by_name(name) if student is None else None

    if student is None and teacher is None:
        print(f"[WARNING] {name} — Excel এ নেই")
        return None

    if teacher is not None:
        roll = teacher["name"]
        sec = str(teacher.get("designation", "Teacher")) 
        sem = ""
    else:
        roll = student["roll"]
        sec = section or student["section"]
        sem = student.get("semester", "") or semester or ""

    if is_duplicate(roll, date_str, course_id):
        return "duplicate"

    status = calculate_status(role, sec, date_str, time_str)

    db = SessionLocal()
    record = Attendance(
        user_id=roll,
        name=name,
        role=role,
        roll_number=roll,
        section=sec,
        date=date_str,
        time=time_str,
        status=status,
        semester=sem,
        course_id=course_id,
        session_id=session_id
    )
    db.add(record)
    db.commit()
    db.close()

    print(f"[ATTENDANCE] Roll: {roll} | {name} | {status} | {date_str} {time_str} | Course: {course_id}")
    return status