from database import SessionLocal, CRAccount

db = SessionLocal()
for c in db.query(CRAccount).all():
    print(c.session_id, c.login_email, c.login_password)
db.close()
