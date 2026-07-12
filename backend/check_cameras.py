from database import SessionLocal, Camera

db = SessionLocal()
cams = db.query(Camera).all()
print(f"মোট {len(cams)} টি camera পাওয়া গেছে।")
for c in cams:
    print(c.id, c.camera_code, "course_id=", c.current_course_id, "session_id=", c.current_session_id)
db.close()
