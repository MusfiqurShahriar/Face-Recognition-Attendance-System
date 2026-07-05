from database import engine, Base, SessionLocal, Session, CRAccount

def migrate():
    # ধাপ ১: cr_account টেবিল তৈরি
    Base.metadata.create_all(engine)
    print("cr_account টেবিল তৈরি হয়েছে।")
    db = SessionLocal()
    try:
        sessions = db.query(Session).order_by(Session.name.asc()).all()
        for s in sessions:
            existing = db.query(CRAccount).filter(CRAccount.session_id == s.id).first()
            if existing:
                print(f"আগে থেকেই CR আছে: {s.name}")
                continue
            email = f"cr.{s.name}@dept.local"
            password = f"cr{s.name.replace('-', '')}"  # যেমন: cr202223
            new_cr = CRAccount(
                session_id=s.id,
                name=f"CR - {s.name}",
                login_email=email,
                login_password=password
            )
            db.add(new_cr)
            print(f"CR তৈরি হলো: {s.name} → email: {email}, password: {password}")
        db.commit()
    finally:
        db.close()

    print("Migration সম্পন্ন হয়েছে।")
if __name__ == "__main__":
    migrate()