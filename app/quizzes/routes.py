from flask import Blueprint, request, jsonify, render_template, session
import google.generativeai as genai
import os, json
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from app.models import quizzes_collection, users_collection, reminders_collection, tasks_collection
from app.reminders.email_utils import send_email
from app.activity_logger import log_activity
import google.generativeai as genai
import random
import json
import os

quiz_bp = Blueprint("quiz", __name__, url_prefix="/quiz")

# Configure Gemini API key


genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash')

@quiz_bp.route("/")
def quiz_ui():
    return render_template("quiz.html")

@quiz_bp.route("/generate", methods=["POST"])
def generate_quiz():
    data = request.get_json()
    subject = data.get('topic')
    num_questions = data.get('num_questions', 25)  # Default to 25 questions

    # Create the prompt for Gemini
    prompt = f"""
        Generate {num_questions} multiple choice quiz questions about {subject}. Each question should:
        1. Be appropriate for a student learning this subject
        2. Have exactly 4 options (A, B, C, D)
        3. Have one correct answer

        Return ONLY a raw JSON array — no markdown, no code fences, no extra text.
        Format:
        [
            {{
                "question": "Question text here",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_answer": "The exact correct option text"
            }}
        ]
        """

    # Generate response from Gemini
    response = model.generate_content(prompt)
    response_text = response.text if response.text else "[]"

    # Strip markdown code fences if present (e.g. ```json ... ```)
    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[-1] if cleaned.count("```") >= 2 else cleaned
        # Remove leading language tag like 'json\n'
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.rsplit("```", 1)[0].strip()

    # Extract the JSON array
    try:
        json_start = cleaned.find('[')
        json_end = cleaned.rfind(']') + 1
        if json_start >= 0 and json_end > json_start:
            questions = json.loads(cleaned[json_start:json_end])
        else:
            questions = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return jsonify({"error": "Failed to parse quiz from AI response", "raw": response_text}), 500

    if not isinstance(questions, list):
        return jsonify({"error": "AI did not return a list of questions", "raw": response_text}), 500

    return jsonify(questions)

@quiz_bp.route('/submit', methods=['POST'])
def submit_quiz():
    data = request.get_json()
    user_id = session.get("user", {}).get("id")
    user_email = session.get("user", {}).get("email")
    user_name = session.get("user", {}).get("name", "there")

    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    subject = data.get('subject', 'General')
    score = data.get('score', 0)  # Percentage 0-100

    # Save quiz result
    quiz_result = {
        "user_id": str(user_id),
        "subject": subject,
        "score": float(score),
        "date": datetime.now().date().isoformat(),
        "created_at": datetime.now(timezone.utc)
    }
    quizzes_collection.insert_one(quiz_result)

    # ── Auto-actions when score < 70% ──────────────────────────────────────
    if float(score) < 70:
        try:
            import pytz
            ist = pytz.timezone("Asia/Kolkata")

            # Schedule reminder for tomorrow at 9:00 AM IST
            now_ist = datetime.now(ist)
            reminder_time_ist = (now_ist + timedelta(days=1)).replace(
                hour=9, minute=0, second=0, microsecond=0
            )
            reminder_time_utc = reminder_time_ist.astimezone(timezone.utc)
            reminder_title = f"Revise {subject} (Quiz score: {int(score)}%)"

            # 1. Add reminder to reminders_collection
            reminders_collection.insert_one({
                "user_id": user_id,
                "email": user_email,
                "title": reminder_title,
                "time": reminder_time_utc,
                "auto": True,
                "source": "quiz_low_score",
                "created_at": datetime.now(timezone.utc)
            })

            # 2. Add subject to planner (user's subjects list)
            users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$addToSet": {"subjects": subject}}
            )

            # 3. Send notification email
            if user_email:
                display_time = reminder_time_ist.strftime("%d %b %Y at %I:%M %p IST")
                email_subject = f"📚 Study Reminder Set: {subject}"
                email_body = (
                    f"Hi {user_name},\n\n"
                    f"You scored {int(score)}% on your {subject} quiz — keep going, you've got this!\n\n"
                    f"To help you improve, we've automatically:\n"
                    f"  \u2705 Added '{subject}' to your Planner\n"
                    f"  \u23f0 Set a revision reminder for {display_time}\n\n"
                    f"Keep pushing \u2014 consistency is the key to mastery.\n\n"
                    f"\u2014 StudyBuddy"
                )
                send_email(user_email, email_subject, email_body)

        except Exception as e:
            # Never let auto-actions break the quiz submission response
            print(f"[QUIZ] Auto-reminder error: {e}", flush=True)

    else:
        # ── Score >= 70%: subject mastered — clean up planner & reminders ──
        try:
            # Remove subject from user's planner subjects list
            users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$pull": {"subjects": subject}}
            )

            # Remove any auto-set reminders for this subject
            reminders_collection.delete_many({
                "user_id": user_id,
                "source": "quiz_low_score",
                "title": {"$regex": f"Revise {subject}", "$options": "i"}
            })

        except Exception as e:
            print(f"[QUIZ] Auto-cleanup error: {e}", flush=True)
    # ───────────────────────────────────────────────────────────────────────

    return jsonify({
        "success": True,
        "message": "Quiz submitted and analyzed.",
        "auto_reminder": float(score) < 70
    })

# @quiz_bp.route('/submit', methods=['POST'])
# def submit_quiz():
#     """Receive quiz results from frontend and store score with user info."""
#     data = request.get_json() or {}
#     score = data.get('score')  # numeric raw score (e.g., 4)
#     total = data.get('total')  # total questions (e.g., 5)
#     percentage = data.get('percentage')  # percentage (0-100)
#     time_taken = data.get('time_taken')  # seconds
#     subject = data.get('subject')
#     topic = data.get('topic')

#     # Resolve user id from session
#     user_id = None
#     if 'user_id' in session:
#         user_id = session['user_id']
#     elif 'user' in session and isinstance(session['user'], dict) and session['user'].get('id'):
#         user_id = session['user'].get('id')

#     if not user_id:
#         return jsonify({'error': 'User not logged in'}), 401

#     try:
#         # Store a quiz-result document
#         quiz_result = {
#             'user_id': str(user_id),
#             'score': float(percentage) if percentage is not None else (float(score) / float(total) * 100 if score is not None and total else 0),
#             'raw_score': score,
#             'total': total,
#             'percentage': float(percentage) if percentage is not None else None,
#             'time_taken_seconds': time_taken,
#             'subject': subject,
#             'topic': topic,
#             'date': datetime.now().date().isoformat(),
#             'created_at': datetime.now()
#         }
#         quizzes_collection.insert_one(quiz_result)
#         return jsonify({'status': 'success', 'inserted': True}), 201
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
