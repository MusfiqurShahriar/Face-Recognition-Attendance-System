from database import SessionLocal, Attendance, Enrollment

db = SessionLocal()
att = db.query(Attendance).filter(
    Attendance.user_id == "200536",
    Attendance.course_id == 20,
    Attendance.session_id == 6
).all()

for a in att:
    print(f"attendance_id={a.id} user_id={a.user_id} course_id={a.course_id} session_id={a.session_id} date={a.date}")

matching_enrollment = db.query(Enrollment).filter(
    Enrollment.user_id == "200536",
    Enrollment.course_id == 20,
    Enrollment.session_id == 6
).first()
print("Matching enrollment এখনো আছে কিনা:", matching_enrollment)
db.close()
