from database import SessionLocal, Session

def seed():
    db = SessionLocal()
    try:
        session_names = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]

        for name in session_names:
            existing = db.query(Session).filter(Session.name == name).first()
            if existing:
                print(f"আগে থেকেই আছে: {name}")
                continue

            new_session = Session(name=name, is_active=1)
            db.add(new_session)
            print(f"যোগ হলো: {name}")

        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed()