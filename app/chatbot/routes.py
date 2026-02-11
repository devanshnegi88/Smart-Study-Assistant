from flask import Blueprint, render_template, request, jsonify, session
import requests, os
from datetime import datetime
from bson import ObjectId
from dotenv import load_dotenv
from app.models import users_collection  # ✅ Import MongoDB collection

# ✅ Load environment variables
load_dotenv()

chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/chatbot")

# ✅ Gemini API Setup
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash-lite:generateContent"

if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY missing! Please add it to your .env file.")

# ==================================================================
# 🧠 Serve Chatbot Page
# ==================================================================
@chatbot_bp.route("/")
def chatbot_page():
    """Serves the chatbot UI page"""
    return render_template("chatbot.html")

# ==================================================================
# ⏱️ Helper: Automatically update study time
# ==================================================================
def update_study_time(user_id, minutes_spent=1):
    """
    Increment user's study time for the current day.
    Called automatically each time chatbot is used.
    """
    today = datetime.now().strftime("%Y-%m-%d")

    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        return

    # ✅ Get existing study time dictionary or create new one
    study_time = user.get("study_time", {})
    today_time = int(study_time.get(today, 0)) + minutes_spent
    study_time[today] = today_time

    # ✅ Update DB
    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"study_time": study_time}}
    )

# ==================================================================
# 🤖 Chatbot API Route (AI Response + Auto Study Tracking)
# ==================================================================
@chatbot_bp.route("/chatbot", methods=["POST"])
def chatbot_api():
    """
    Handles chatbot queries + automatically logs study time
    whenever user interacts with chatbot.
    """
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    # ✅ Update study time for logged-in user
    if "user" in session:
        user_id = session["user"]["id"]
        update_study_time(user_id)  # Adds +1 minute or call frequency count

    # ✅ Prepare payload for Gemini API
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "You are an AI study assistant. "
                            "Answer only study-related or educational questions clearly and concisely. "
                            "If the user asks something unrelated to academics, politely decline.\n\n"
                            f"User: {user_message}"
                        )
                    }
                ]
            }
        ]
    }

    # ✅ Send request to Gemini API
    try:
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        response.raise_for_status()
        result = response.json()

        # ✅ Extract reply
        reply = (
            result.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "Sorry, no response found.")
        )

        return jsonify({"response": reply})

    except Exception as e:
        print("Error:", e)
        return jsonify({"error": "Something went wrong with the Gemini API."}), 500
