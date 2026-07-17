from database import Base, engine, Course, Enrollment, Camera, CameraCommand

def migrate():
    print(f"[INFO] Connected DB: {str(engine.url)[:30]}...")

    confirm = input(
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