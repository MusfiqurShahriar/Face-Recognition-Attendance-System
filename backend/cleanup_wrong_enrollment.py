from database import SessionLocal, Enrollment

db = SessionLocal()
wrong_rolls = ["200536", "210507", "220524", "220536"]

deleted = db.query(Enrollment).filter(
    Enrollment.user_id.in_(wrong_rolls),
    Enrollment.session_id == 6
).delete(synchronize_session=False)

db.commit()
print(f"[OK] {deleted} টি ভুল enrollment মুছে ফেলা হয়েছে (session_id=6 থেকে)।")
db.close()
