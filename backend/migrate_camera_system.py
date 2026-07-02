from database import engine, Base, SessionLocal, Camera

def migrate():
    # ধাপ ১: নতুন টেবিল (camera, camera_command) তৈরি
    Base.metadata.create_all(engine)
    print("নতুন টেবিল (camera, camera_command) তৈরি হয়েছে।")

    # ধাপ ২: ৪টা camera seed করা
    db = SessionLocal()
    try:
        camera_rooms = ["804", "805", "806", "807"]

        for room in camera_rooms:
            existing = db.query(Camera).filter(Camera.camera_code == room).first()
            if existing:
                print(f"আগে থেকেই আছে: Room {room}")
                continue

            new_camera = Camera(camera_code=room, room_name=f"Room {room}")
            db.add(new_camera)
            print(f"যোগ হলো: Room {room}")

        db.commit()
    finally:
        db.close()

    print("Migration সম্পন্ন হয়েছে।")

if __name__ == "__main__":
    migrate()