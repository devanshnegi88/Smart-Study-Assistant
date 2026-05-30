# pyrefly: ignore [missing-import]
from flask import Blueprint, request, jsonify, render_template, session
from bson import ObjectId
from datetime import datetime, timezone
import os
import pytz
from app.models import reminders_collection
from app.reminders.email_utils import send_email

reminders_bp = Blueprint("reminders", __name__, url_prefix="/reminders")

@reminders_bp.route("/")
def home():
    return render_template("reminder.html")

@reminders_bp.route("/api", methods=["GET"])
def get_reminders():
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["user"]["id"]
    now = datetime.utcnow()

    reminders = list(reminders_collection.find({
        "user_id": user_id,
        "time": {"$gte": now}
    }).sort("time", 1))

    for r in reminders:
        r["_id"] = str(r["_id"])

    return jsonify(reminders)

@reminders_bp.route("/add", methods=["POST"])
def add_reminder():
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.json
    user = session["user"]
    
    try:
        local_time = datetime.fromisoformat(data["time"].replace("Z", "+00:00"))
        utc_time = local_time.astimezone(timezone.utc)
    except Exception as e:
        return jsonify({"error": f"Invalid time format: {e}"}), 400

    title = data.get("title", "Reminder")
    
    result = reminders_collection.insert_one({
        "user_id": user["id"],
        "email": user.get("email"),
        "title": title,
        "time": utc_time
    })
    reminder_id = result.inserted_id

    # Send confirmation email to the user
    user_email = user.get("email")
    if user_email:
        # Format the time in a readable way (keep it in UTC, or convert to IST)
        try:
            ist = pytz.timezone("Asia/Kolkata")
            display_time = utc_time.astimezone(ist).strftime("%d %b %Y at %I:%M %p IST")
        except Exception:
            display_time = utc_time.strftime("%d %b %Y at %H:%M UTC")

        email_subject = f"⏰ Reminder Set: {title}"
        email_body = (
            f"Hi {user.get('name', 'there')},\n\n"
            f"Your reminder has been successfully set!\n\n"
            f"  📌 Title   : {title}\n"
            f"  🕐 Time    : {display_time}\n\n"
            f"We will notify you when the time comes.\n\n"
            f"— StudyBuddy Reminders"
        )
        send_email(user_email, email_subject, email_body)

    return jsonify({"status": "success", "id": str(reminder_id)}), 201

@reminders_bp.route("/<reminder_id>", methods=["DELETE"])
def delete_reminder(reminder_id):
    reminders_collection.delete_one({"_id": ObjectId(reminder_id)})
    return jsonify({"message": "Deleted"})

@reminders_bp.route("/cleanup", methods=["POST"])
def cleanup_expired():
    now = datetime.now(timezone.utc)
    result = reminders_collection.delete_many({"time": {"$lt": now}})
    return jsonify({"deleted": result.deleted_count})
