from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from database import SessionLocal, Attendance

teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")

@teacher_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "teacher":
        return redirect(url_for("auth.login"))

    db = SessionLocal()

    records = db.query(Attendance).filter(
        Attendance.name == current_user.name,
        Attendance.role == "teacher"
    ).order_by(Attendance.date.desc()).all()

    total_classes = len(records)

    from datetime import datetime
    current_month = datetime.now().strftime("%Y-%m")
    monthly_records = [r for r in records if r.date.startswith(current_month)]

    db.close()
    return render_template("teacher/dashboard.html",
        records=records,
        total_classes=total_classes,
        monthly_count=len(monthly_records),
        current_month=current_month
    )