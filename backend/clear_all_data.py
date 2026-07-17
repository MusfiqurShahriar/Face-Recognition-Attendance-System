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