from sqlalchemy import text
from database import engine, Base  # তোমার database.py থেকে import

def migrate():
    # ধাপ ১: নতুন টেবিল (session, course, enrollment) তৈরি
    Base.metadata.create_all(engine)
    print("নতুন টেবিল (session, course, enrollment) তৈরি হয়েছে।")
    # ধাপ ২: existing টেবিলে (attendance, class_session) column যোগ
    with engine.connect() as conn:
        for table in ["attendance", "class_session"]:
            for col_name, col_type in [("course_id", "INTEGER"), ("session_id", "INTEGER")]:
                try:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    print(f"যোগ হলো: {table}.{col_name}")
                except Exception as e:
                    print(f"Skip ({table}.{col_name}): {e}")

    print("Migration সম্পন্ন হয়েছে।")
if __name__ == "__main__":
    migrate()