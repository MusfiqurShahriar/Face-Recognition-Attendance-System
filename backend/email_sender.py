import smtplib
import ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import SessionLocal, Attendance, load_students_from_excel
from dotenv import load_dotenv
from datetime import date
import requests as http_requests

load_dotenv()

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_NAME = "Face Recognition Attendance System"
BREVO_SMTP = os.getenv("BREVO_SMTP")
BREVO_LOGIN = os.getenv("BREVO_LOGIN")
BREVO_PASSWORD = os.getenv("BREVO_PASSWORD")

def send_email(to_email, subject, body):
    try:
        api_key = os.getenv("BREVO_API_KEY")
        
        response = http_requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": api_key,
                "Content-Type": "application/json"
            },
            json={
                "sender": {"name": SENDER_NAME, "email": SENDER_EMAIL},
                "to": [{"email": to_email}],
                "subject": subject,
                "htmlContent": body
            },
            timeout=30
        )
        
        if response.status_code == 201:
            return True
        else:
            print(f"[ERROR] Brevo API error: {response.text}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Email পাঠানো যায়নি {to_email} — {e}")
        return False

def send_absent_notifications(target_date=None):
    if not target_date:
        target_date = date.today().strftime("%Y-%m-%d")
    db = SessionLocal()
    present_rolls = db.query(Attendance.roll_number).filter(
        Attendance.date == target_date,
        Attendance.role == "student"
    ).all()
    present_rolls = [p[0] for p in present_rolls]
    db.close()
    all_students = load_students_from_excel()
    absent_students = [s for s in all_students if s["roll"] not in present_rolls]

    success_count = 0
    fail_count = 0

    for student in absent_students:
        guardian_email = student.get("guardian_email", "")
        if not guardian_email or guardian_email == "nan":
            continue
        subject = f"⚠️ অনুপস্থিতির বিজ্ঞপ্তি — {student['name']} — {target_date}"
        body = f"""
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px;
                    margin: 0 auto; padding: 20px; background: #f9f9f9;">
            <div style="background: white; border-radius: 8px;
                        padding: 28px; border: 1px solid #e0e0e0;">

                <div style="border-left: 4px solid #e74c3c; padding-left: 16px; margin-bottom: 20px;">
                    <h2 style="color: #e74c3c; margin: 0 0 4px;">অনুপস্থিতির বিজ্ঞপ্তি</h2>
                    <p style="color: #888; margin: 0; font-size: 13px;">
                        Face Recognition Attendance System
                    </p>
                </div>

                <p style="color: #333; font-size: 15px;">
                    সম্মানিত অভিভাবক,
                </p>

                <p style="color: #333; font-size: 15px; line-height: 1.6;">
                    আপনার সন্তান <strong>{student['name']}</strong>
                    আজ <strong>{target_date}</strong> তারিখে
                    ক্লাসে অনুপস্থিত ছিল।
                </p>

                <div style="background: #f8f8f8; border-radius: 8px;
                            padding: 16px; margin: 20px 0;">
                    <table style="width: 100%; font-size: 14px;">
                        <tr>
                            <td style="color: #888; padding: 4px 0;">নাম</td>
                            <td style="color: #333; font-weight: bold;
                                    text-align: right;">{student['name']}</td>
                        </tr>
                        <tr>
                            <td style="color: #888; padding: 4px 0;">Roll</td>
                            <td style="color: #333; font-weight: bold;
                                    text-align: right;">{student['roll']}</td>
                        </tr>
                        <tr>
                            <td style="color: #888; padding: 4px 0;">Section</td>
                            <td style="color: #333; font-weight: bold;
                                    text-align: right;">{student['section']}</td>
                        </tr>
                        <tr>
                            <td style="color: #888; padding: 4px 0;">তারিখ</td>
                            <td style="color: #333; font-weight: bold;
                                    text-align: right;">{target_date}</td>
                        </tr>
                    </table>
                </div>

                <p style="color: #555; font-size: 13px; line-height: 1.6;">
                    যদি এটি ভুল তথ্য হয় বা কোনো প্রশ্ন থাকে,
                    অনুগ্রহ করে বিভাগীয় দপ্তরে যোগাযোগ করুন।
                </p>

                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">

                <p style="color: #aaa; font-size: 11px; text-align: center;">
                    এটি একটি স্বয়ংক্রিয় বার্তা।
                    Face Recognition Attendance System দ্বারা প্রেরিত।
                </p>
            </div>
        </body>
        </html>
        """

        result = send_email(guardian_email, subject, body)
        if result:
            success_count += 1
            print(f"[OK] Guardian email → {student['name']} ({guardian_email})")
        else:
            fail_count += 1

    return {
        "total_absent": len(absent_students),
        "success": success_count,
        "failed": fail_count,
        "date": target_date
    }