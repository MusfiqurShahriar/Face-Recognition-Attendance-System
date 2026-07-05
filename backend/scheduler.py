import schedule
import time
from backup import create_backup
from datetime import datetime

print("[INFO] Backup scheduler चालू হয়েছে")
print("[INFO] প্রতিদিন রাত ১১টায় backup নেওয়া হবে")

# টেস্ট করার জন্য এখনই জোর করে একবার ব্যাকআপ রান করা হচ্ছে
print("[DEBUG] গুগল ড্রাইভ লগইন ভেরিফিকেশনের জন্য এখনই ব্যাকআপ রান করা হচ্ছে...")
create_backup()
# প্রতিদিন রাত ১১টায় backup নেবে
schedule.every().day.at("23:00").do(create_backup)

while True:
    schedule.run_pending()
    time.sleep(60)