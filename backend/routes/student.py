from flask import Blueprint, render_template
from flask_login import login_required, current_user
from database import SessionLocal, Attendance
from database import SessionLocal, Attendance, Course, Enrollment

student_bp = Blueprint("student", __name__, url_prefix="/student")

@student_bp.route("/courses")
@login_required
def my_courses():
    if current_user.role != "student":
        from flask import redirect, url_for
        return redirect(url_for("admin.dashboard"))

    db = SessionLocal()
    try:
        enrollments = db.query(Enrollment).filter(
            Enrollment.user_id == current_user.id
        ).all()
        course_ids = [e.course_id for e in enrollments]
        courses = db.query(Course).filter(Course.id.in_(course_ids)).all()
    finally:
        db.close()

    return render_template("student/courses.html", courses=courses)

@student_bp.route("/course/<int:course_id>/dashboard")
@login_required
def course_dashboard(course_id):
    if current_user.role != "student":
        from flask import redirect, url_for
        return redirect(url_for("admin.dashboard"))

    db = SessionLocal()
    try:
        course_obj = db.query(Course).get(course_id)

        records = db.query(Attendance).filter(
            Attendance.user_id == current_user.id,
            Attendance.course_id == course_id
        ).order_by(Attendance.date).all()

        total_days = db.query(Attendance.date).filter(
            Attendance.role == "student",
            Attendance.course_id == course_id
        ).distinct().count()

        present_count = len(records)
        percentage = round((present_count / total_days * 100), 1) if total_days > 0 else 0

        on_time = len([r for r in records if r.status == "On Time"])
        late = len([r for r in records if r.status == "Late"])
    finally:
        db.close()

    return render_template("student/dashboard.html",
        course=course_obj,
        records=records,
        total_days=total_days,
        present_count=present_count,
        percentage=percentage,
        on_time=on_time,
        late=late
    )