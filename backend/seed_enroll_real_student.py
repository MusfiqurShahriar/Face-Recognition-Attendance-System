from database import SessionLocal, Enrollment

def seed():
    db = SessionLocal()
    try:
        existing = db.query(Enrollment).filter(
            Enrollment.course_id == 1,
            Enrollment.user_id == "230508"
        ).first()

        if existing:
            print("এই student আগে থেকেই enrolled আছে।")
        else:
            enrollment = Enrollment(
                course_id=1,          # আগের seed script এ বানানো CSE101 কোর্স
                user_id="230508",     # current_user.id এর সাথে মিলতে হবে
                name="Test Student 230508",
                roll_number="230508"
            )
            db.add(enrollment)
            db.commit()
            print(f"Enroll হলো: roll 230508, course_id=1")
    finally:
        db.close()

if __name__ == "__main__":
    seed()