from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from database import SessionLocal, Camera, Course, CameraCommand, Attendance, Enrollment
from functools import wraps
from datetime import datetime

cr_bp = Blueprint("cr", __name__, url_prefix="/cr")
def cr_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role != "cr":
            flash("এই পেজ দেখার অনুমতি আপনার নেই।", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated

@cr_bp.route("/dashboard", methods=["GET", "POST"])
@login_required
@cr_required
def dashboard():
    db = SessionLocal()
    try:
        if request.method == "POST":
            camera_id = request.form.get("camera_id")
            course_id = request.form.get("course_id")

            if not camera_id or not course_id:
                flash("Camera এবং Course দুইটাই সিলেক্ট করুন!", "error")
            else:
                new_command = CameraCommand(
                    camera_id=camera_id,
                    course_id=course_id,
                    session_id=current_user.session_id,
                    status="pending"
                )
                db.add(new_command)
                db.commit()
                flash("Camera command পাঠানো হয়েছে!", "success")

        # POST/GET উভয় ক্ষেত্রেই শেষে fresh query করা হচ্ছে
        cameras = db.query(Camera).order_by(Camera.camera_code).all()
        courses = db.query(Course).filter(
            Course.session_id == current_user.session_id
        ).order_by(Course.course_code).all()

    finally:
        db.close()
    return render_template("cr/dashboard.html", cameras=cameras, courses=courses)

@cr_bp.route("/course/<int:course_id>/report")
@login_required
@cr_required
def course_report(course_id):
    db = SessionLocal()
    try:
        course_obj = db.query(Course).get(course_id)

        # নিরাপত্তা: CR শুধু তার নিজের session-এর course-ই দেখতে পারবে
        if not course_obj or course_obj.session_id != current_user.session_id:
            flash("এই কোর্সটি আপনার session-এর অন্তর্গত নয়।", "error")
            return redirect(url_for("cr.dashboard"))

        enrolled = db.query(Enrollment).filter(Enrollment.course_id == course_id).all()

        all_dates = db.query(Attendance.date).filter(
            Attendance.role == "student",
            Attendance.course_id == course_id
        ).distinct().all()
        total_days = len(all_dates)

        report = []
        for e in enrolled:
            present_count = db.query(Attendance).filter(
                Attendance.course_id == course_id,
                Attendance.roll_number == e.roll_number
            ).count()
            percentage = round((present_count / total_days * 100), 1) if total_days > 0 else 0
            report.append({
                "roll": e.roll_number,
                "name": e.name,
                "present": present_count,
                "total": total_days,
                "percentage": percentage
            })
        report = sorted(report, key=lambda x: x["roll"] or "")
    finally:
        db.close()
    return render_template("cr/course_report.html", course=course_obj, report=report, total_days=total_days)

@cr_bp.route("/course/<int:course_id>/export")
@login_required
@cr_required
def course_export(course_id):
    from openpyxl.styles import PatternFill, Font
    from openpyxl.utils import get_column_letter
    import io, pandas as pd
    from flask import send_file

    db = SessionLocal()
    try:
        course_obj = db.query(Course).get(course_id)
        if not course_obj or course_obj.session_id != current_user.session_id:
            flash("এই কোর্সটি আপনার session-এর অন্তর্গত নয়।", "error")
            return redirect(url_for("cr.dashboard"))
        enrolled = db.query(Enrollment).filter(Enrollment.course_id == course_id).all()

        all_dates = db.query(Attendance.date).filter(
            Attendance.role == "student",
            Attendance.course_id == course_id
        ).distinct().all()
        total_days = len(all_dates)

        report = []
        for e in enrolled:
            present_count = db.query(Attendance).filter(
                Attendance.course_id == course_id,
                Attendance.roll_number == e.roll_number
            ).count()
            percentage = round((present_count / total_days * 100), 1) if total_days > 0 else 0
            report.append({
                "roll": e.roll_number,
                "name": e.name,
                "present": present_count,
                "total": total_days,
                "percentage": percentage
            })
        report = sorted(report, key=lambda x: x["roll"] or "")

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            wb = writer.book
            ws = wb.create_sheet("Percentage")
            headers = ["Roll", "Name", "Present", "Total", "Percentage"]
            ws.append(headers)

            header_fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True)
            for col in range(1, len(headers) + 1):
                cell = ws.cell(row=1, column=col)
                cell.fill = header_fill
                cell.font = header_font

            for row_idx, r in enumerate(report, start=2):
                ws.cell(row=row_idx, column=1, value=r["roll"])
                ws.cell(row=row_idx, column=2, value=r["name"])
                ws.cell(row=row_idx, column=3, value=r["present"])
                ws.cell(row=row_idx, column=4, value=r["total"])
                ws.cell(row=row_idx, column=5, value=f'{r["percentage"]}%')

            for col in range(1, len(headers) + 1):
                ws.column_dimensions[get_column_letter(col)].width = 20

            if "Sheet" in wb.sheetnames:
                wb.remove(wb["Sheet"])

        output.seek(0)
        filename = f"{course_obj.course_code}_percentage.xlsx"
    finally:
        db.close()
    return send_file(
        output,
        download_name=filename,
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )