from database import SessionLocal, Attendance

db = SessionLocal()
null_count = db.query(Attendance).filter(Attendance.session_id == None).count()
total_count = db.query(Attendance).count()
print(f"মোট Attendance: {total_count}, session_id NULL: {null_count}")
db.close()
