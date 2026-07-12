from database import SessionLocal, CRAccount, Session

db = SessionLocal()
print("--- Sessions ---")
for s in db.query(Session).all():
    print(s.id, repr(s.name))

print("--- CR Accounts ---")
for c in db.query(CRAccount).all():
    print(c.id, c.session_id, repr(c.login_email), repr(c.login_password))
db.close()
