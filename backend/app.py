from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_required
from database import init_db, get_student_by_email, get_admin_from_env, get_teacher_by_email, load_students_from_excel, load_teachers_from_excel
from attendance_manager import mark_attendance
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

app = Flask(
    __name__,
    template_folder="../frontend/templates",
    static_folder="../frontend/static"
)
app.secret_key = "face_attendance_secret_key_2024"
from datetime import timedelta
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(days=7)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "আগে login করুন।"

class LoginUser:
    def __init__(self, data, role):
        self.id = data.get("roll", data.get("name", "admin"))
        self.name = data["name"]
        self.email = data["login_email"]
        self.role = role
        self.roll_number = data.get("roll", None)
        self.section = data.get("section", None)
        self.session_id = data.get("session_id", None)
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False

    def get_id(self):
        return f"{self.role}:{self.email}"

@login_manager.user_loader
def load_user(user_id):
    if ":" not in user_id:
        return None
    role, email = user_id.split(":", 1)
    if role == "admin":
        admin = get_admin_from_env()
        if admin["login_email"] == email:
            return LoginUser(admin, "admin")
    elif role == "student":
        student = get_student_by_email(email)
        if student:
            return LoginUser(student, "student")
    elif role == "teacher":
        teacher = get_teacher_by_email(email)
        if teacher:
            return LoginUser(teacher, "teacher")
    elif role == "cr":
        from database import get_cr_by_email
        cr = get_cr_by_email(email)
        if cr:
            return LoginUser(cr, "cr")
    return None

@app.after_request
def skip_ngrok_warning(response):
    response.headers["ngrok-skip-browser-warning"] = "69420"
    return response

# ==========================================
# API Endpoint for Remote Face Recognition
# ==========================================
@app.route("/api/mark-attendance", methods=["POST"])
def api_mark_attendance():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400
        
    name = data.get("name")
    role = data.get("role")
    semester = data.get("semester")
    course_id = data.get("course_id")
    session_id = data.get("session_id")
    
    if not name or not role:
        return jsonify({"status": "error", "message": "Missing name or role"}), 400
        
    result = mark_attendance(name=name, role=role, semester=semester, course_id=course_id, session_id=session_id)
    
    if result == "duplicate":
        return jsonify({"status": "duplicate", "message": "Already marked"})
    elif result:
        return jsonify({"status": "success", "status_message": result})
    else:
        return jsonify({"status": "error", "message": "Failed to mark attendance"})
@app.route("/api/camera-command/<camera_code>", methods=["GET"])
def get_camera_command(camera_code):
    from database import SessionLocal, Camera, CameraCommand, Course

    db = SessionLocal()
    try:
        camera = db.query(Camera).filter(Camera.camera_code == camera_code).first()
        if not camera:
            return {"status": "error", "message": "Camera পাওয়া যায়নি"}, 404

        command = db.query(CameraCommand).filter(
            CameraCommand.camera_id == camera.id,
            CameraCommand.status == "pending"
        ).order_by(CameraCommand.created_at.desc()).first()

        if not command:
            return {"status": "no_command"}, 200

        course = db.query(Course).get(command.course_id)

        command.status = "acknowledged"
        db.commit()

        return {
            "status": "success",
            "course_id": command.course_id,
            "session_id": command.session_id,
            "course_code": course.course_code if course else None
        }, 200
    finally:
        db.close()

# ==========================================
# SMART BULK & MANUAL ATTENDANCE CONTROLLER
# ==========================================
# আপনার কোড স্ট্রাকচার অনুযায়ী এই রাউটটি /routes/admin.py ফাইলে থাকতে পারে। 
# যদি সেখানে থাকে, তবে এই ফাংশনটি শুধু কেটে নিয়ে সেখানে বসিয়ে দিন।
@app.route("/admin/manual-attendance", methods=["POST"])
def manual_attendance_fallback():
    from database import SessionLocal, Attendance, load_students_from_excel, load_teachers_from_excel
    from flask import request, flash, redirect
    from datetime import datetime

    role = request.form.get("role")
    identifier = request.form.get("identifier", "").strip()
    status = request.form.get("status", "On Time")
    custom_date = request.form.get("date")

    if not custom_date:
        custom_date = datetime.now().strftime("%Y-%m-%d")
    
    time_str = datetime.now().strftime("%I:%M %p")
    db = SessionLocal()

    try:
        # ১. "All" সিলেক্ট করলে সব স্টুডেন্টের হাজিরা
        if role == "student" and identifier.lower() == "all":
            all_students = load_students_from_excel()
            count = 0
            for student in all_students:
                exists = db.query(Attendance).filter(Attendance.name == student["name"], Attendance.date == custom_date).first()
                if not exists:
                    new_record = Attendance(
                        user_id=student.get("roll", student["name"]),
                        name=student["name"],
                        role="student",
                        roll_number=student.get("roll", ""),
                        section=student.get("section", ""),
                        date=custom_date,
                        time=time_str,
                        status=status,
                        semester=student.get("semester", "")
                    )
                    db.add(new_record)
                    count += 1
            db.commit()
            flash(f"সফলভাবে মোট {count} জন শিক্ষার্থীর বাল্ক হাজিরা নেওয়া হয়েছে।", "success")
        
        # ২. সিঙ্গেল স্টুডেন্ট বা টিচারের হাজিরা
        # ২. সিঙ্গেল স্টুডেন্ট বা টিচারের হাজিরা
        else:
            target_name = identifier
            target_roll = ""
            target_section = ""
            target_semester = ""
            db_role = "student" if role == "student" else "teacher"

            if role == "student":
                all_students = load_students_from_excel()
                # স্মার্ট সার্চ: রোল অথবা নাম যেকোনো একটা দিলেই স্টুডেন্টকে খুঁজে বের করবে
                student_match = next((s for s in all_students if str(s.get("roll")) == identifier or s.get("name").lower() == identifier.lower()), None)
                
                if student_match:
                    target_name = student_match["name"]
                    target_roll = student_match.get("roll", "")
                    target_section = student_match.get("section", "")
                    target_semester = student_match.get("semester", "")
                else:
                    # যদি ভুল নাম বা রোল দেয়, তবে ডেটা সেভ না করে এরর মেসেজ দেবে
                    flash(f"দুঃখিত, '{identifier}' নামে বা রোলে কোনো স্টুডেন্ট ডাটাবেজে পাওয়া যায়নি!", "danger")
                    return redirect("/admin/dashboard")
            else:
                all_teachers = load_teachers_from_excel()
                teacher_match = next((t for t in all_teachers if t["name"].lower() == identifier.lower()), None)
                
                if teacher_match:
                    target_name = teacher_match["name"]
                    target_section = teacher_match.get("designation", "")
                else:
                    flash(f"দুঃখিত, '{identifier}' নামে কোনো শিক্ষক পাওয়া যায়নি!", "danger")
                    return redirect("/admin/dashboard")

            # ডুপ্লিকেট চেক
            exists = db.query(Attendance).filter(Attendance.name == target_name, Attendance.date == custom_date).first()
            if exists:
                flash(f"দুঃখিত, {target_name} এর হাজিরা আজ আগেই নেওয়া হয়েছে!", "danger")
            else:
                new_record = Attendance(
                    user_id=target_roll if target_roll else target_name,
                    name=target_name,
                    role=db_role,
                    roll_number=target_roll,
                    section=target_section,
                    date=custom_date,
                    time=time_str,
                    status=status,
                    semester=target_semester
                )
                db.add(new_record)
                db.commit()
                flash(f"সফলভাবে {target_name} এর ম্যানুয়াল হাজিরা নেওয়া হয়েছে।", "success")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

    # রিডাইরেক্ট করে ড্যাশবোর্ডে পাঠিয়ে দেবে
    return redirect("/admin/dashboard")


from routes.admin import admin_bp
from routes.student import student_bp
from routes.auth import auth_bp
from routes.teacher import teacher_bp
from routes.cr import cr_bp
app.register_blueprint(cr_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(student_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(teacher_bp)

@app.route("/keep-alive")
def keep_alive():
    from database import SessionLocal
    from sqlalchemy import text
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return "Server and Database are awake!", 200
    except Exception as e:
        return f"Error waking up DB: {str(e)}", 500
    finally:
        db.close()


from flask_login import login_required

@app.route('/about')
@login_required
def about():
    return render_template('about.html')

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)