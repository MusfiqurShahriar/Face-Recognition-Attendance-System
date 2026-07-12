from database import SessionLocal, Enrollment

db = SessionLocal()
total = db.query(Enrollment).count()
print(f"মোট Enrollment: {total}")

for e in db.query(Enrollment).limit(10).all():
    print(e.id, "course_id=", e.course_id, "session_id=", e.session_id, "roll=", e.roll_number, "name=", e.name)
db.close()
