from database import SessionLocal, Course

db = SessionLocal()
for c in db.query(Course).all():
    print(c.id, repr(c.semester), c.course_code, c.course_name)
db.close()
