from database import SessionLocal, Session, Course, Enrollment

def seed():
    db = SessionLocal()
    try:
        # টেস্ট সেশন
        test_session = Session(name="2022-23", is_active=1)
        db.add(test_session)
        db.commit()
        db.refresh(test_session)
        print(f"Session তৈরি হলো: {test_session.name} (id={test_session.id})")

        # টেস্ট কোর্স
        test_course = Course(
            session_id=test_session.id,
            course_code="CSE101",
            course_name="Introduction to Programming",
            section="22-23"
        )
        db.add(test_course)
        db.commit()
        db.refresh(test_course)
        print(f"Course তৈরি হলো: {test_course.course_name} (id={test_course.id})")

        # একটা টেস্ট enrollment (এখানে তোমার কোনো real student এর roll/name বসাও)
        test_enrollment = Enrollment(
            course_id=test_course.id,
            user_id="TEST001",
            name="Test Student",
            roll_number="TEST001"
        )
        db.add(test_enrollment)
        db.commit()
        print(f"Enrollment তৈরি হলো: {test_enrollment.name}")

    finally:
        db.close()

if __name__ == "__main__":
    seed()
