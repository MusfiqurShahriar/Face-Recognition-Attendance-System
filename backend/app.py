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

# API Endpoint for Remote Face Recognition
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

        # আগে pending command চেক করো (নতুন command থাকলে সেটাই প্রাধান্য পাবে)
        command = db.query(CameraCommand).filter(
            CameraCommand.camera_id == camera.id,
            CameraCommand.status == "pending"
        ).order_by(CameraCommand.created_at.desc()).first()

        if command:
            command.status = "acknowledged"
            camera.current_course_id = command.course_id
            camera.current_session_id = command.session_id
            db.commit()
            course_id = command.course_id
            session_id = command.session_id
        elif camera.current_course_id is not None:
            # কোনো নতুন pending command নেই, কিন্তু camera-র শেষ known course আছে
            # restart/reconnect হলেও এটা দিয়ে camera সঠিক course এ কাজ চালিয়ে যাবে
            course_id = camera.current_course_id
            session_id = camera.current_session_id
        else:
            return {"status": "no_command"}, 200

        course = db.query(Course).get(course_id)

        return {
            "status": "success",
            "course_id": course_id,
            "session_id": session_id,
        }, 200
    finally:
        db.close()

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