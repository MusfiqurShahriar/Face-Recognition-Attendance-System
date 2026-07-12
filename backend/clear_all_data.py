"""
এই স্ক্রিপ্টটা backend ফোল্ডারের ভেতরে রেখে চালাতে হবে
(database.py যেখানে আছে সেই একই লেভেলে বা সেখান থেকে import করা যায় এমন জায়গায়)

চালানোর নিয়ম (PowerShell থেকে, venv activate করা অবস্থায়):
    python clear_all_data.py

এটা কী করে:
- .env থেকে DATABASE_URL পড়ে (আপনার ক্ষেত্রে এটা Neon/Postgres হওয়ার কথা)
- Base.metadata তে যত টেবিল আছে, সবগুলো থেকে row delete করে
- Foreign key নির্ভরতা অনুযায়ী সঠিক ক্রমে delete করে (আগে child, পরে parent) যাতে
  FK constraint violation না হয়
- Table structure/schema অক্ষত থাকে, শুধু data মুছে যায়
"""

from database import Base, engine, SessionLocal

def clear_all_data():
    db = SessionLocal()
    try:
        print(f"[INFO] Connected DB: {str(engine.url)[:30]}...")

        confirm = input(
            "\n⚠️  এটা connected database-এর সব টেবিলের সব data মুছে ফেলবে (structure থাকবে)।\n"
            "নিশ্চিত হলে 'yes' লিখুন: "
        )
        if confirm.strip().lower() != "yes":
            print("[CANCELLED] কিছু মুছা হয়নি।")
            return

        # metadata.sorted_tables দেয় parent-first ক্রম (FK নির্ভরতা অনুযায়ী)
        # তাই delete করার সময় সেটা reverse করে child-first করা হচ্ছে
        tables_in_delete_order = list(reversed(Base.metadata.sorted_tables))

        for table in tables_in_delete_order:
            result = db.execute(table.delete())
            print(f"[OK] '{table.name}' থেকে {result.rowcount} row মুছা হয়েছে")

        db.commit()
        print("\n✅ সব টেবিলের data সফলভাবে মুছে ফেলা হয়েছে। Table structure অক্ষত আছে।")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] সমস্যা হয়েছে, কিছুই মুছা হয়নি (rollback করা হলো): {e}")
    finally:
        db.close()

if __name__ == "__main__":
    clear_all_data()