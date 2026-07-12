"""
এই স্ক্রিপ্টটা backend ফোল্ডারে (database.py এর পাশে) রেখে চালাতে হবে।

চালানোর নিয়ম:
    python migrate_course_enrollment.py

এটা কী করে:
- 'camera_command', 'camera', 'enrollment', 'course' — এই টেবিলগুলো সঠিক ক্রমে DROP করে
  (কারণ camera/camera_command টেবিল course-কে FK দিয়ে reference করে, তাই আগে সেগুলো drop করতে হবে)
- database.py এর নতুন model অনুযায়ী আবার নতুন করে বানায় (বিপরীত ক্রমে)
- session, attendance, class_sessions, cr_account টেবিল touch করে না, অক্ষত থাকে

⚠️ সতর্কতা: camera, camera_command, course, enrollment — এই চারটা টেবিলের বর্তমান সব data মুছে যাবে।
   (যেহেতু আপনি ইতিমধ্যে পুরো DB wipe করেছেন, এই মুহূর্তে risk নেই)
"""

from database import Base, engine, Course, Enrollment, Camera, CameraCommand

def migrate():
    print(f"[INFO] Connected DB: {str(engine.url)[:30]}...")

    confirm = input(
        "\n⚠️  এটা 'camera_command', 'camera', 'enrollment', 'course' টেবিল ড্রপ করে "
        "নতুন structure দিয়ে আবার বানাবে (এই টেবিলগুলোর বর্তমান সব data মুছে যাবে)।\n"
        "নিশ্চিত হলে 'yes' লিখুন: "
    )
    if confirm.strip().lower() != "yes":
        print("[CANCELLED] কিছুই করা হয়নি।")
        return

    print("[INFO] পুরনো টেবিলগুলো সঠিক ক্রমে ড্রপ করা হচ্ছে...")
    CameraCommand.__table__.drop(bind=engine, checkfirst=True)
    Camera.__table__.drop(bind=engine, checkfirst=True)
    Enrollment.__table__.drop(bind=engine, checkfirst=True)
    Course.__table__.drop(bind=engine, checkfirst=True)
    print("[OK] পুরনো টেবিল ড্রপ হয়েছে।")

    print("[INFO] নতুন structure দিয়ে টেবিল তৈরি করা হচ্ছে...")
    Course.__table__.create(bind=engine, checkfirst=True)
    Enrollment.__table__.create(bind=engine, checkfirst=True)
    Camera.__table__.create(bind=engine, checkfirst=True)
    CameraCommand.__table__.create(bind=engine, checkfirst=True)
    print("[OK] নতুন টেবিলগুলো তৈরি হয়েছে।")

    print("\n✅ Migration সম্পূর্ণ।")

if __name__ == "__main__":
    migrate()