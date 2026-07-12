from flask import Blueprint, render_template
from flask_login import login_required, current_user
from database import SessionLocal, Attendance, Course, Enrollment, Session

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

        # student এর নিজের batch বের করা হচ্ছে (current_user.section এ আসলে batch/session name থাকে,
        # যেমন "2022-23" — এটা load_students_from_excel() এর "section" key থেকে আসে)
        student_session_id = None
        if current_user.section:
            student_session_obj = db.query(Session).filter(Session.name == current_user.section).first()
            if student_session_obj:
                student_session_id = student_session_obj.id

        records_query = db.query(Attendance).filter(
            Attendance.user_id == current_user.id,
            Attendance.course_id == course_id
        )
        total_days_query = db.query(Attendance.date).filter(
            Attendance.role == "student",
            Attendance.course_id == course_id
        )

        # student এর batch খুঁজে পাওয়া গেলে, সেই batch এর মধ্যেই আটকে রাখা হচ্ছে
        # (নাহলে ভবিষ্যতে এই course অন্য batch শেয়ার করলে percentage ভুল হিসাব হবে)
        if student_session_id is not None:
            records_query = records_query.filter(Attendance.session_id == student_session_id)
            total_days_query = total_days_query.filter(Attendance.session_id == student_session_id)

        records = records_query.order_by(Attendance.date).all()
        total_days = total_days_query.distinct().count()

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