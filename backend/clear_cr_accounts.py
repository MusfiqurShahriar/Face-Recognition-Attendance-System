from database import SessionLocal, CRAccount

db = SessionLocal()
db.query(CRAccount).delete()
db.commit()
print("[OK] সব পুরনো CR account মোছা হয়েছে।")
db.close()
