from database import SessionLocal, Session, Course

def get_or_create_session_id(db, name):
    s = db.query(Session).filter(Session.name == name).first()
    return s.id if s else None

def add_course(db, session_id, code, name, section=None):
    existing = db.query(Course).filter(
        Course.session_id == session_id,
        Course.course_code == code,
        Course.section == section
    ).first()
    if existing:
        print(f"আগে থেকেই আছে: {code} - {name}")
        return
    c = Course(session_id=session_id, course_code=code, course_name=name, section=section)
    db.add(c)
    print(f"যোগ হলো: {code} - {name}")

def seed():
    db = SessionLocal()
    try:
        sessions = {
            "2020-21": get_or_create_session_id(db, "2020-21"),
            "2021-22": get_or_create_session_id(db, "2021-22"),
            "2022-23": get_or_create_session_id(db, "2022-23"),
            "2023-24": get_or_create_session_id(db, "2023-24"),
            "2024-25": get_or_create_session_id(db, "2024-25"),
        }

        for name, sid in sessions.items():
            if not sid:
                print(f"⚠️ Session পাওয়া যায়নি: {name}, স্কিপ করা হলো")

        # ================= 2020-21 (4th Year 2nd Sem) =================
        sid = sessions["2020-21"]
        if sid:
            add_course(db, sid, "EECE4211", "Computer Networks and Data Communication")
            add_course(db, sid, "EECE4212", "Sessional Based on Computer Networks and Data Communication")
            add_course(db, sid, "EECE4221", "Measurement and Instrumentation")
            add_course(db, sid, "EECE4222", "Sessional Based on Measurement and Instrumentation")
            add_course(db, sid, "EECE4231", "Digital Communication")
            add_course(db, sid, "EECE4232", "Sessional Based on Digital Communication")
            add_course(db, sid, "EECE42XX", "Elective IV", section="IV")
            add_course(db, sid, "EECE42XX", "Elective V", section="V")

        # ================= 2021-22 (4th Year 1st Sem) =================
        sid = sessions["2021-22"]
        if sid:
            add_course(db, sid, "EECE4111", "Digital Signal Processing")
            add_course(db, sid, "EECE4112", "Sessional Based on Digital Signal Processing")
            add_course(db, sid, "EECE4121", "Wireless and Mobile Communication")
            add_course(db, sid, "EECE4122", "Sessional Based on Wireless and Mobile Communication")
            add_course(db, sid, "EECE41XX", "Elective I", section="I")
            add_course(db, sid, "EECE41XX", "Sessional Based on Elective I", section="I-S")
            add_course(db, sid, "EECE41XX", "Elective II", section="II")
            add_course(db, sid, "EECE41XX", "Sessional Based on Elective II", section="II-S")
            add_course(db, sid, "EECE41XX", "Elective III", section="III")
            add_course(db, sid, "EECE41XX", "Sessional Based on Elective III", section="III-S")
            add_course(db, sid, "EECE4181", "Industrial Training")

        # ================= 2022-23 (3rd Year 1st Sem) =================
        sid = sessions["2022-23"]
        if sid:
            add_course(db, sid, "EECE3111", "Electromagnetic Fields and Waves")
            add_course(db, sid, "EECE3121", "Industrial and Power Electronics")
            add_course(db, sid, "EECE3122", "Sessional Based on Industrial and Power Electronics")
            add_course(db, sid, "EECE3131", "Communication Fundamentals")
            add_course(db, sid, "EECE3132", "Sessional Based on Communication Fundamentals")
            add_course(db, sid, "EECE3141", "Power System I")
            add_course(db, sid, "EECE3142", "Sessional Based on Power System I")
            add_course(db, sid, "EECE3151", "Control System")

        # ================= 2023-24 (2nd Year 2nd Sem) =================
        sid = sessions["2023-24"]
        if sid:
            add_course(db, sid, "EECE2211", "Digital Electronics")
            add_course(db, sid, "EECE2212", "Sessional Based on Digital Electronics")
            add_course(db, sid, "EECE2221", "Electrical Machine II")
            add_course(db, sid, "EECE2222", "Sessional Based on Electrical Machine II")
            add_course(db, sid, "EECE2231", "Pulse and Switching Circuits")
            add_course(db, sid, "EECE2232", "Sessional Based on Pulse and Switching Circuits")
            add_course(db, sid, "MATH2201", "Special Functions and Numerical Methods")
            add_course(db, sid, "HUM2201", "Economics")
            add_course(db, sid, "EECE2242", "Electrical and Electronic Workshop")

        # ================= 2024-25 (1st Year 2nd Sem) =================
        sid = sessions["2024-25"]
        if sid:
            add_course(db, sid, "EECE1211", "Electrical Circuits II")
            add_course(db, sid, "EECE1212", "Sessional Based on Electrical Circuits II")
            add_course(db, sid, "EECE1221", "Electronics I")
            add_course(db, sid, "EECE1222", "Sessional Based on Electronics I")
            add_course(db, sid, "CSE1201", "Computer Fundamental and Programming")
            add_course(db, sid, "CSE1202", "Sessional Based on Computer Fundamental and Programming")
            add_course(db, sid, "STAT1201", "Statistics")
            add_course(db, sid, "MATH1201", "Integral Calculus and Differential Equations")

        db.commit()
        print("\n✅ সব course যোগ করা সম্পন্ন হয়েছে!")
    finally:
        db.close()

if __name__ == "__main__":
    seed()