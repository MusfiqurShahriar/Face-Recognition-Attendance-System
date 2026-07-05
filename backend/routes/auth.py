from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from database import get_student_by_email, get_admin_from_env
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from database import get_cr_by_email
import os
load_dotenv()
auth_bp = Blueprint("auth", __name__)

SECRET_KEY = "attendance_reset_secret_2024"
serializer = URLSafeTimedSerializer(SECRET_KEY)
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

def send_reset_email(to_email, reset_link):
    try:
        SENDER_EMAIL = os.getenv("SENDER_EMAIL")
        BREVO_SMTP = os.getenv("BREVO_SMTP")
        BREVO_PORT = int(os.getenv("BREVO_PORT", 587))
        BREVO_LOGIN = os.getenv("BREVO_LOGIN")
        BREVO_PASSWORD = os.getenv("BREVO_PASSWORD")

        msg = MIMEMultipart("alternative")
        msg["From"] = f"Face Recognition Attendance System <{SENDER_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = "Password Reset — Face Recognition Attendance System"

        body = f"""
        <html>
        <body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
            <div style="background:white;border-radius:8px;padding:28px;border:1px solid #e0e0e0">
                <h2 style="color:#6366f1">Password Reset</h2>
                <p>আপনি password reset এর request করেছেন।</p>
                <p>নিচের button এ click করুন:</p>
                <a href="{reset_link}"
                style="background:#6366f1;color:white;padding:12px 24px;
                        border-radius:8px;text-decoration:none;display:inline-block;
                        margin:16px 0">
                    Password Reset করুন
                </a>
                <p style="color:#888;font-size:12px">
                    এই link ১৫ মিনিট পর্যন্ত valid থাকবে।<br>
                    আপনি যদি এই request না করে থাকেন তাহলে ignore করুন।
                </p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, "html", "utf-8"))
        server = smtplib.SMTP(BREVO_SMTP, BREVO_PORT)
        server.ehlo()
        server.starttls()
        server.login(BREVO_LOGIN, BREVO_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"[ERROR] Reset email পাঠানো যায়নি — {e}")
        return False

@auth_bp.route("/", methods=["GET", "POST"])
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        admin = get_admin_from_env()
        admin_email2 = os.getenv("ADMIN_EMAIL2", "")

        if (email == admin["login_email"] or email == admin_email2) and password == admin["login_password"]:
            user = LoginUser(admin, "admin")
            login_user(user)
            return redirect(url_for("admin.dashboard"))

        cr = get_cr_by_email(email)
        if cr and cr["login_password"] == password:
            user = LoginUser(cr, "cr")
            login_user(user)
            return redirect(url_for("cr.dashboard"))

        student = get_student_by_email(email)
        if student and student["login_password"] == password:
            user = LoginUser(student, "student")
            login_user(user)
            return redirect(url_for("student.my_courses"))
        from database import get_teacher_by_email
        teacher = get_teacher_by_email(email)
        if teacher and teacher["login_password"] == password:
            user = LoginUser(teacher, "teacher")
            login_user(user)
            return redirect(url_for("teacher.dashboard"))
        flash("Email বা Password ভুল!", "error")
    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        admin = get_admin_from_env()
        admin_email2 = os.getenv("ADMIN_EMAIL2", "")

        if email == admin["login_email"] or email == admin_email2:
            token = serializer.dumps(email, salt="password-reset")
            reset_link = url_for("auth.reset_password", token=token, _external=True)
            actual_email = os.getenv("ADMIN_EMAIL2") or admin["login_email"]
            result = send_reset_email(actual_email, reset_link)
            if result:
                flash("Reset link তোমার Gmail এ পাঠানো হয়েছে!", "success")
            else:
                flash("Email পাঠাতে সমস্যা হয়েছে!", "error")
        else:
            flash("এই email দিয়ে কোনো Admin account নেই!", "error")
    return render_template("forgot_password.html")

@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = serializer.loads(token, salt="password-reset", max_age=900)
    except SignatureExpired:
        flash("Reset link এর মেয়াদ শেষ হয়ে গেছে!", "error")
        return redirect(url_for("auth.forgot_password"))
    except BadSignature:
        flash("Invalid reset link!", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        new_pass = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")

        if new_pass != confirm:
            flash("Password দুটো মিলছে না!", "error")
            return redirect(url_for("auth.reset_password", token=token))

        if len(new_pass) < 6:
            flash("Password কমপক্ষে ৬ অক্ষরের হতে হবে!", "error")
            return redirect(url_for("auth.reset_password", token=token))

        env_path = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", ".env"
        ))

        with open(env_path, "r") as f:
            lines = f.readlines()

        with open(env_path, "w") as f:
            for line in lines:
                if line.startswith("ADMIN_PASSWORD="):
                    f.write(f"ADMIN_PASSWORD={new_pass}\n")
                else:
                    f.write(line)
        load_dotenv(env_path, override=True)
        flash("Password সফলভাবে পরিবর্তন হয়েছে! এখন login করুন।", "success")
        return redirect(url_for("auth.login"))
    return render_template("reset_password.html", token=token)