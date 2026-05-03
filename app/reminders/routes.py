from flask import Blueprint, request, jsonify, render_template, session
from bson import ObjectId
from datetime import datetime, timezone
from app.models import reminders_collection
from app.reminders.email_utils import send_email
import os
import pytz
import traceback
import sys
from threading import Thread
import time
from threading import Thread
from datetime import datetime, timezone
import time

# --- New imports for scheduler/email ---
from threading import Thread
import time
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import pytz
import traceback

# Load environment variables
load_dotenv()

reminders_bp = Blueprint("reminders", __name__, url_prefix="/reminders")

# connect to MongoDB Atlas
@reminders_bp.route("/")
def home():
    return render_template("reminder.html")

# 🕒 Ensure TTL index exists
# This deletes documents automatically after their 'time' passes
reminders_collection.create_index("time", expireAfterSeconds=0)

# ✅ Fetch active reminders
# @reminders_bp.route("/api", methods=["GET"])
# def get_reminders():

#     if 'user' not in session:
#         user_id = ObjectId("68ec90bf4699cec6b75a735e")
#     else:
#         user_id = ObjectId(session['user']['id'])

#     now = datetime.utcnow()
#     reminders = list(reminders_collection.find({"time": {"$gt": now}}))
#     for r in reminders:
#         r["_id"] = str(r["_id"])
#     return jsonify(reminders)

@reminders_bp.route("/api", methods=["GET"])
def get_reminders():
<<<<<<< HEAD
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_email = session["user"]["email"]
    now = datetime.utcnow()

    reminders = list(reminders_collection.find({
        "user.email": user_email,   # only this user's reminders
        "time": {"$gte": now}        # not expired (TTL already deletes expired)
    }).sort("time", 1))

    for r in reminders:
        r["_id"] = str(r["_id"])

    return jsonify(reminders)


# ✅ Add a new reminder
# @reminders_bp.route("/add", methods=["POST"])
# def add_reminder():
#     if "user" not in session:
#         return jsonify({"error": "Not logged in"}), 401

#     data = request.json

#     # Convert frontend local time to UTC before saving
#     local_time = datetime.fromisoformat(data["time"])
#     utc_time = local_time.astimezone(timezone.utc)

#     result = reminders_collection.insert_one({
#         "user": session["user"],
#         "title": data["title"],
#         "time": utc_time
#     })

#     return jsonify({
#         "status": "success",
#         "_id": str(result.inserted_id),
#         "title": data["title"],
#         "time": data["time"]  # send back original local time for UI
#     }), 201

@reminders_bp.route("/add", methods=["POST"])
def add_reminder():
    import sys
    sys.stderr.write("[REMINDER] /add route called\n")
    sys.stderr.flush()
    
    if "user" not in session:
        sys.stderr.write("[REMINDER] ⚠ User not in session\n")
        sys.stderr.flush()
        return jsonify({"error": "Not logged in"}), 401

    data = request.json
    sys.stderr.write(f"[REMINDER] Request data: {data}\n")
    sys.stderr.flush()
    
=======
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_email = session["user"]["email"]
    now = datetime.utcnow()

    reminders = list(reminders_collection.find({
        "user.email": user_email,   # only this user's reminders
        "time": {"$gte": now}        # not expired (TTL already deletes expired)
    }).sort("time", 1))

    for r in reminders:
        r["_id"] = str(r["_id"])

    return jsonify(reminders)


# ✅ Add a new reminder
# @reminders_bp.route("/add", methods=["POST"])
# def add_reminder():
#     if "user" not in session:
#         return jsonify({"error": "Not logged in"}), 401

#     data = request.json

#     # Convert frontend local time to UTC before saving
#     local_time = datetime.fromisoformat(data["time"])
#     utc_time = local_time.astimezone(timezone.utc)

#     result = reminders_collection.insert_one({
#         "user": session["user"],
#         "title": data["title"],
#         "time": utc_time
#     })

#     return jsonify({
#         "status": "success",
#         "_id": str(result.inserted_id),
#         "title": data["title"],
#         "time": data["time"]  # send back original local time for UI
#     }), 201

@reminders_bp.route("/add", methods=["POST"])
def add_reminder():
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.json
>>>>>>> 84e29029a03bff646e1397431a9616823050952e
    local_time = datetime.fromisoformat(data["time"])
    utc_time = local_time.astimezone(timezone.utc)

    user = session["user"]
<<<<<<< HEAD
    title = data.get("title", "Reminder")
    priority = data.get("priority", "normal")
    sys.stderr.write(f"[REMINDER] User object: {user}\n")
    sys.stderr.write(f"[REMINDER] User email: {user.get('email')}, Title: {title}\n")
    sys.stderr.flush()
=======
>>>>>>> 84e29029a03bff646e1397431a9616823050952e

    reminders_collection.insert_one({
        "user": {
            "id": user["id"],
<<<<<<< HEAD
            "email": user["email"]
        },
        "title": title,
        "time": utc_time,
        "priority": priority,
        "auto": False,
        "notify_flags": {}
    })
    sys.stderr.write("[REMINDER] Reminder saved to DB\n")
    sys.stderr.flush()

    # Notify the user immediately when a reminder is created.
    if user.get("email"):
        sys.stderr.write(f"[REMINDER] Email found: {user.get('email')}, proceeding with email send\n")
        sys.stderr.flush()
        timezone_name = os.getenv("DEFAULT_TZ", "UTC")
        try:
            local_time = utc_time.astimezone(pytz.timezone(timezone_name))
        except Exception:
            local_time = utc_time

        subject = f"Reminder created: {title}"
        body = (
            f"Hello,\n\n"
            f"Your reminder \"{title}\" has been created for {local_time.strftime('%Y-%m-%d %H:%M (%Z)')}.\n\n"
            "We will remind you before the scheduled time.\n\n"
            "— Smart Study Planner"
        )
        sys.stderr.write(f"[REMINDER] About to call send_email({user['email']}, {subject})\n")
        sys.stderr.flush()
        result = send_email(user["email"], subject, body)
        sys.stderr.write(f"[REMINDER] send_email returned: {result}\n")
        sys.stderr.flush()
    else:
        sys.stderr.write("[REMINDER] ⚠ No email found for user\n")
        sys.stderr.flush()

    return jsonify({"status": "success"}), 201

=======
            "email": user["email"]   # must store email for filtering
        },
        "title": data["title"],
        "time": utc_time
    })

    return jsonify({"status": "success"}), 201

>>>>>>> 84e29029a03bff646e1397431a9616823050952e

# ✅ Delete a reminder manually
@reminders_bp.route("/<reminder_id>", methods=["DELETE"])
def delete_reminder(reminder_id):
    reminders_collection.delete_one({"_id": ObjectId(reminder_id)})
    return jsonify({"message": "Deleted"})

<<<<<<< HEAD

# ✅ Cleanup expired reminders (called by frontend periodically)
@reminders_bp.route("/cleanup", methods=["POST"])
def cleanup_expired():
    print("[REMINDER] Cleanup triggered", flush=True)
    now = datetime.now(timezone.utc)
    result = reminders_collection.delete_many({"time": {"$lt": now}})
    print(f"[REMINDER] Deleted {result.deleted_count} expired reminders", flush=True)
    return jsonify({"deleted": result.deleted_count})

# ------------------------------
# Background email scheduler (ENABLED)
# ------------------------------
DEFAULT_TZ = os.getenv("DEFAULT_TZ", "Asia/Kolkata")
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))

def reminder_scheduler():
    tz = pytz.timezone(DEFAULT_TZ)
    print("[SCHEDULER] Reminder scheduler started. Poll interval:", POLL_INTERVAL_SECONDS, "seconds. TZ:", DEFAULT_TZ, flush=True)

    while True:
        try:
            now_utc = datetime.now(timezone.utc)
            cursor = reminders_collection.find({"time": {"$gt": now_utc}})
            checked = 0

            for doc in cursor:
                checked += 1
                try:
                    reminder_id = doc.get("_id")
                    title = doc.get("title", "No Title")
                    user = doc.get("user") or {}
                    to_email = user.get("email") if isinstance(user, dict) else doc.get("email")

                    if not to_email or not doc.get("time"):
                        continue

                    notify_flags = doc.get("notify_flags", {}) or {}

                    delta = doc["time"] - now_utc
                    hours_left = delta.total_seconds() / 3600.0
                    days_left = delta.total_seconds() / (3600.0 * 24.0)

                    local_time = doc["time"].astimezone(tz)
                    local_time_str = local_time.strftime("%Y-%m-%d %H:%M (%Z)")

                    # 4-hour reminder
                    if 0 < hours_left <= 4 and not notify_flags.get("four_hour"):
                        subject = f"Reminder — '{title}' in ~{int(hours_left)}h"
                        body = f"Hello! '{title}' at {local_time_str}. Coming in {int(hours_left)}h. — Smart Study Planner"
                        if send_email(to_email, subject, body):
                            notify_flags["four_hour"] = True
                            reminders_collection.update_one({"_id": reminder_id}, {"$set": {"notify_flags": notify_flags}})

                    # Daily for >1 day away
                    elif days_left > 1:
                        today_str = datetime.now(tz).date().isoformat()
                        if notify_flags.get("daily") != today_str:
                            subject = f"Daily: '{title}' on {local_time.strftime('%Y-%m-%d')}"
                            body = f"Daily reminder for '{title}' at {local_time_str}. — Smart Study Planner"
                            if send_email(to_email, subject, body):
                                notify_flags["daily"] = today_str
                                reminders_collection.update_one({"_id": reminder_id}, {"$set": {"notify_flags": notify_flags}})
                except Exception as sub_e:
                    print(f"[SCHEDULER] Error on reminder {reminder_id}: {sub_e}", flush=True)

            print(f"[SCHEDULER] Checked {checked} reminders at {now_utc.isoformat()}", flush=True)
        except Exception as e:
            print(f"[SCHEDULER] Loop error: {e}", flush=True)

        time.sleep(POLL_INTERVAL_SECONDS)

# Start scheduler ALWAYS (dev-friendly)
try:
    scheduler_thread = Thread(target=reminder_scheduler, daemon=True)
    scheduler_thread.start()
    print("[SCHEDULER] ✅ Background thread started successfully!", flush=True)
except Exception as e:
    print(f"[SCHEDULER] ❌ Failed to start: {e}", flush=True)
=======
# ------------------------------
# Background email scheduler code
# ------------------------------
>>>>>>> 84e29029a03bff646e1397431a9616823050952e

# Environment-configurable values
# MAIL_SERVER = os.getenv("MAIL_SERVER")
# MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
# MAIL_USERNAME = os.getenv("MAIL_USERNAME")
# MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
# MAIL_FROM = os.getenv("MAIL_FROM") or MAIL_USERNAME
# MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() in ("1", "true", "yes")
# MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "false").lower() in ("1", "true", "yes")

# DEFAULT_TZ = os.getenv("DEFAULT_TZ", "Asia/Kolkata")  # used to format times in email
# POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))  # default 5 minutes

# def send_email(to_email: str, subject: str, body: str) -> bool:
#     """
#     Sends an email using SMTP settings from environment.
#     Returns True if send succeeded.
#     """
#     if not MAIL_SERVER or not MAIL_USERNAME or not MAIL_PASSWORD:
#         print("[EMAIL] SMTP not configured (MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD required).")
#         return False

#     try:
#         msg = EmailMessage()
#         msg["From"] = MAIL_FROM
#         msg["To"] = to_email
#         msg["Subject"] = subject
#         msg.set_content(body)

#         if MAIL_USE_SSL:
#             server = smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT, timeout=30)
#         else:
#             server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=30)

#         server.ehlo()
#         if MAIL_USE_TLS and not MAIL_USE_SSL:
#             server.starttls()
#             server.ehlo()

#         server.login(MAIL_USERNAME, MAIL_PASSWORD)
#         server.send_message(msg)
#         server.quit()
#         print(f"[EMAIL] Sent to {to_email}: {subject}")
#         return True
#     except Exception as e:
#         print("[EMAIL] Send failed:", e)
#         traceback.print_exc()
#         return False

# def reminder_scheduler():
#     """
#     Background loop:
#       - For each future reminder:
#          * if >1 day away: send daily email once per day (flag: notify_flags.daily = 'YYYY-MM-DD')
#          * if <=4 hours away and >0: send one 4-hour email (flag: notify_flags.four_hour = True)
#       - Update reminder documents with notify_flags to avoid duplicates.
#     """
#     tz = pytz.timezone(DEFAULT_TZ)
#     print("[SCHEDULER] Reminder scheduler started. Poll interval:", POLL_INTERVAL_SECONDS, "seconds. TZ:", DEFAULT_TZ)

#     while True:
#         try:
#             now_utc = datetime.now(timezone.utc)
#             cursor = reminders_collection.find({"time": {"$gt": now_utc}})
#             checked = 0

#             for doc in cursor:
#                 checked += 1
#                 try:
#                     reminder_id = doc.get("_id")
#                     title = doc.get("title", "No Title")
#                     user = doc.get("user") or {}
#                     to_email = None
#                     # user can be a dict containing email or the doc may contain email field
#                     if isinstance(user, dict):
#                         to_email = user.get("email")
#                     if not to_email:
#                         to_email = doc.get("email")

#                     reminder_time = doc.get("time")
#                     if not reminder_time:
#                         continue

#                     # notifications flags stored per reminder to prevent duplicates
#                     notify_flags = doc.get("notify_flags", {}) or {}

#                     # compute time left
#                     delta = reminder_time - now_utc
#                     hours_left = delta.total_seconds() / 3600.0
#                     days_left = delta.total_seconds() / (3600.0 * 24.0)

#                     # friendly local time for email
#                     local_time = reminder_time.astimezone(tz)
#                     local_time_str = local_time.strftime("%Y-%m-%d %H:%M (%Z)")

#                     # 1) 4-hour email
#                     if 0 < hours_left <= 4 and not notify_flags.get("four_hour", False):
#                         if to_email:
#                             subject = f"Reminder — '{title}' in about {int(max(1, hours_left))} hour(s)"
#                             body = (
#                                 f"Hello,\n\n"
#                                 f"This is a reminder that \"{title}\" is scheduled at {local_time_str}.\n\n"
#                                 f"It's coming up in approximately {int(max(1, hours_left))} hour(s).\n\n"
#                                 "— Smart Study Planner"
#                             )
#                             sent = send_email(to_email, subject, body)
#                             if sent:
#                                 notify_flags["four_hour"] = True
#                                 reminders_collection.update_one({"_id": reminder_id}, {"$set": {"notify_flags": notify_flags}})
#                         else:
#                             print(f"[SCHEDULER] no email for reminder {reminder_id} ('{title}'), skipping 4-hour mail.")

#                     # 2) Daily email for reminders more than 1 day away
#                     elif days_left > 1:
#                         today_str = datetime.now(tz).date().isoformat()
#                         last_daily = notify_flags.get("daily")  # yyyy-mm-dd of last daily sent
#                         if last_daily != today_str:
#                             if to_email:
#                                 subject = f"Daily reminder — '{title}' on {local_time.strftime('%Y-%m-%d')}"
#                                 body = (
#                                     f"Hello,\n\n"
#                                     f"This is your daily reminder for \"{title}\" scheduled at {local_time_str}.\n\n"
#                                     "We'll keep reminding you daily until 24 hours before the event.\n\n"
#                                     "— Smart Study Planner"
#                                 )
#                                 sent = send_email(to_email, subject, body)
#                                 if sent:
#                                     notify_flags["daily"] = today_str
#                                     reminders_collection.update_one({"_id": reminder_id}, {"$set": {"notify_flags": notify_flags}})
#                             else:
#                                 print(f"[SCHEDULER] no email for reminder {reminder_id} ('{title}'), skipping daily mail.")
#                     # else: either within (4,24] hours -> do nothing until 4-hour mark, or negative -> TTL will remove
#                 except Exception as sub_e:
#                     print("[SCHEDULER] error handling reminder:", sub_e)
#                     traceback.print_exc()

#             print(f"[SCHEDULER] scan complete at {datetime.now(timezone.utc).isoformat()} — checked {checked} reminders.")
#         except Exception as e:
#             print("[SCHEDULER] main loop error:", e)
#             traceback.print_exc()

#         time.sleep(POLL_INTERVAL_SECONDS)

# # Start scheduler in background thread.
# # Guard against starting twice when Flask auto-reloader runs: only start in the reloader child process.
# # Werkzeug sets WERKZEUG_RUN_MAIN in the child; start when this equals 'true' OR when not using reloader.
# _start_scheduler = False
# if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or os.environ.get("WERKZEUG_RUN_MAIN") is None:
#     _start_scheduler = True

# # Also allow explicit disabling via env
# if os.getenv("START_REMINDER_SCHEDULER", "true").lower() in ("0", "false", "no"):
#     _start_scheduler = False

# if _start_scheduler:
#     try:
#         scheduler_thread = Thread(target=reminder_scheduler, daemon=True)
#         scheduler_thread.start()
#         print("[SCHEDULER] background thread started.")
#     except Exception as e:
#         print("[SCHEDULER] failed to start thread:", e)
#         traceback.print_exc()
# else:
#     print("[SCHEDULER] not started (WERKZEUG_RUN_MAIN check or START_REMINDER_SCHEDULER disabled).")
