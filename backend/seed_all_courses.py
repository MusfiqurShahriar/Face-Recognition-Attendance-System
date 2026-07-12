from database import SessionLocal, Course

def add_course(db, semester, code, name):
    existing = db.query(Course).filter(
        Course.semester == semester,
        Course.course_code == code
    ).first()
    if existing:
        print(f"আগে থেকেই আছে: {code} - {name}")
        return
    c = Course(semester=semester, course_code=code, course_name=name)
    db.add(c)
    print(f"যোগ হলো ({semester}): {code} - {name}")

def seed():
    db = SessionLocal()
    try:
        # 4th Year 2nd Semester
        sem = "4th Year 2nd Semester"
        add_course(db, sem, "EECE4211", "Computer Networks and Data Communication")
        add_course(db, sem, "EECE4212", "Sessional Based on Computer Networks and Data Communication")
        add_course(db, sem, "EECE4221", "Measurement and Instrumentation")
        add_course(db, sem, "EECE4222", "Sessional Based on Measurement and Instrumentation")
        add_course(db, sem, "EECE4231", "Digital Communication")
        add_course(db, sem, "EECE4232", "Sessional Based on Digital Communication")
        add_course(db, sem, "EECE42XX-IV", "Elective IV")
        add_course(db, sem, "EECE42XX-V", "Elective V")

        # 4th Year 1st Semester
        sem = "4th Year 1st Semester"
        add_course(db, sem, "EECE4111", "Digital Signal Processing")
        add_course(db, sem, "EECE4112", "Sessional Based on Digital Signal Processing")
        add_course(db, sem, "EECE4121", "Wireless and Mobile Communication")
        add_course(db, sem, "EECE4122", "Sessional Based on Wireless and Mobile Communication")
        add_course(db, sem, "EECE41XX-I", "Elective I")
        add_course(db, sem, "EECE41XX-IS", "Sessional Based on Elective I")
        add_course(db, sem, "EECE41XX-II", "Elective II")
        add_course(db, sem, "EECE41XX-IIS", "Sessional Based on Elective II")
        add_course(db, sem, "EECE41XX-III", "Elective III")
        add_course(db, sem, "EECE41XX-IIIS", "Sessional Based on Elective III")
        add_course(db, sem, "EECE4181", "Industrial Training")

        # 3rd Year 2nd Semester
        sem = "3rd Year 2nd Semester"
        add_course(db, sem, "EECE3211", "Radio and TV Engineering")
        add_course(db, sem, "EECE3221", "Telecommunication Engineering")
        add_course(db, sem, "EECE3222", "Sessional Based on Telecommunication Engineering")
        add_course(db, sem, "EECE3231", "Microprocessor and Embedded System")
        add_course(db, sem, "EECE3232", "Sessional Based on Microprocessor and Embedded System")
        add_course(db, sem, "EECE3241", "Signals and Systems")
        add_course(db, sem, "EECE3242", "Sessional Based on Signals and Systems")
        add_course(db, sem, "EECE3251", "VLSI Circuits and Design")
        add_course(db, sem, "EECE3252", "Sessional Based on VLSI Circuits and Design")

        # 3rd Year 1st Semester
        sem = "3rd Year 1st Semester"
        add_course(db, sem, "EECE3111", "Electromagnetic Fields and Waves")
        add_course(db, sem, "EECE3121", "Industrial and Power Electronics")
        add_course(db, sem, "EECE3122", "Sessional Based on Industrial and Power Electronics")
        add_course(db, sem, "EECE3131", "Communication Fundamentals")
        add_course(db, sem, "EECE3132", "Sessional Based on Communication Fundamentals")
        add_course(db, sem, "EECE3141", "Power System I")
        add_course(db, sem, "EECE3142", "Sessional Based on Power System I")
        add_course(db, sem, "EECE3151", "Control System")

        # 2nd Year 2nd Semester
        sem = "2nd Year 2nd Semester"
        add_course(db, sem, "EECE2211", "Digital Electronics")
        add_course(db, sem, "EECE2212", "Sessional Based on Digital Electronics")
        add_course(db, sem, "EECE2221", "Electrical Machine II")
        add_course(db, sem, "EECE2222", "Sessional Based on Electrical Machine II")
        add_course(db, sem, "EECE2231", "Pulse and Switching Circuits")
        add_course(db, sem, "EECE2232", "Sessional Based on Pulse and Switching Circuits")
        add_course(db, sem, "MATH2201", "Special Functions and Numerical Methods")
        add_course(db, sem, "HUM2201", "Economics")
        add_course(db, sem, "EECE2242", "Electrical and Electronic Workshop")

        # 2nd Year 1st Semester
        sem = "2nd Year 1st Semester"
        add_course(db, sem, "EECE2111", "Electronics II")
        add_course(db, sem, "EECE2112", "Sessional Based on Electronics II")
        add_course(db, sem, "EECE2121", "Electrical Properties of Materials")
        add_course(db, sem, "EECE2131", "Electrical Machine I")
        add_course(db, sem, "HUM2101", "Bangladesh Studies")
        add_course(db, sem, "HUM2111", "Industrial Management and Accounting")
        add_course(db, sem, "MATH2101", "Linear Algebra and Vector Analysis")

        # 1st Year 2nd Semester
        sem = "1st Year 2nd Semester"
        add_course(db, sem, "EECE1211", "Electrical Circuits II")
        add_course(db, sem, "EECE1212", "Sessional Based on Electrical Circuits II")
        add_course(db, sem, "EECE1221", "Electronics I")
        add_course(db, sem, "EECE1222", "Sessional Based on Electronics I")
        add_course(db, sem, "CSE1201", "Computer Fundamental and Programming")
        add_course(db, sem, "CSE1202", "Sessional Based on Computer Fundamental and Programming")
        add_course(db, sem, "STAT1201", "Statistics")
        add_course(db, sem, "MATH1201", "Integral Calculus and Differential Equations")

        # 1st Year 1st Semester
        sem = "1st Year 1st Semester"
        add_course(db, sem, "EECE1111", "Electrical Circuits I")
        add_course(db, sem, "EECE1112", "Sessional Based on Electrical Circuits I")
        add_course(db, sem, "PHY1101", "Physics")
        add_course(db, sem, "CE1101", "Engineering Graphics")
        add_course(db, sem, "HUM1101", "English")
        add_course(db, sem, "MATH1101", "Differential Calculus and Analytical Geometry")
        add_course(db, sem, "CHEM1101", "Physical and Inorganic Chemistry")

        db.commit()
        print("\n✅ সব course যোগ করা সম্পন্ন হয়েছে!")
    finally:
        db.close()

if __name__ == "__main__":
    seed()