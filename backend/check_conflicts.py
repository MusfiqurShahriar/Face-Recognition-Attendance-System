from database import SessionLocal, Enrollment

db = SessionLocal()
rolls_to_check = ["200536", "210507", "220524", "220536"]

for roll in rolls_to_check:
    print(f"\n--- Roll {roll} ---")
    for e in db.query(Enrollment).filter(Enrollment.user_id == roll).all():
        print(f"  enrollment_id={e.id} course_id={e.course_id} session_id={e.session_id} name={e.name}")
db.close()
