from flask import Blueprint, request, jsonify, render_template, session
import google.generativeai as genai
import os, json
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from app.models import quizzes_collection, users_collection, reminders_collection, tasks_collection
from app.reminders.email_utils import send_email
from app.activity_logger import log_activity

quiz_bp = Blueprint("quiz", __name__, url_prefix="/quiz")

# Configure Gemini API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

@quiz_bp.route("/")
def quiz_ui():
    return render_template("quiz.html")

@quiz_bp.route("/generate", methods=["POST"])
def generate_quiz():
    data = request.json
    topic = data.get("topic")
    num_questions = data.get("num_questions", 5)

    if not topic:
        return jsonify({"error": "Topic is required"}), 400

    prompt = f"""
    Generate {num_questions} multiple choice questions on the topic "{topic}".
    Return the output as a **valid JSON list**.
    Each question must follow this schema:
    [
      {{
        "question": "string",
        "options": ["A","B","C","D"],
        "correct_answer": "string"
      }}
    ]
    Make sure each option is EXACTLY ONE LETTER (A, B, C, or D).
    Do NOT return code blocks or markdown formatting.
    Return ONLY the JSON array.
    """

    try:
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        response = model.generate_content(prompt)
        text_response = response.text.strip()

        # Clean up response - remove markdown code blocks
        if text_response.startswith("```"):
            text_response = text_response.split("```")[1]
            if text_response.startswith("json"):
                text_response = text_response[4:]
        text_response = text_response.strip()

        # Try parsing as JSON
        try:
            quiz_data = json.loads(text_response)
            if not isinstance(quiz_data, list):
                return jsonify({"error": "Quiz data must be a list"}), 500
            
            return jsonify(quiz_data)
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            print(f"Response was: {text_response[:200]}")
            return jsonify({"error": f"Failed to parse quiz: {str(e)}"}), 500

    except Exception as e:
        print(f"Error generating quiz: {str(e)}")
        return jsonify({"error": str(e)}), 500

@quiz_bp.route("/history")
def quiz_history():
    quizzes = list(quizzes_collection.find({}, {"_id": 0}))
    return jsonify(quizzes)


LOW_PERFORMANCE_THRESHOLD = float(os.getenv("LOW_PERFORMANCE_THRESHOLD", 60))
AUTO_REMINDER_HOURS = int(os.getenv("AUTO_REMINDER_HOURS", 24))


def _make_review_reminder_time():
    now = datetime.now(timezone.utc)
    reminder_time = now + timedelta(hours=AUTO_REMINDER_HOURS)
    return reminder_time.replace(minute=0, second=0, microsecond=0)


def _create_weak_topic_task(user_id, subject):
    task_date = (datetime.now().date() + timedelta(days=1)).isoformat()
    tasks_collection.insert_one({
        "user_id": str(user_id),
        "task_name": f"Review weak topic: {subject}",
        "date": task_date,
        "priority": "high",
        "notes": "Weak topic detected after low quiz performance.",
        "created_at": datetime.now(timezone.utc)
    })


def _create_auto_reminder(user_id, email, subject):
    reminder_time = _make_review_reminder_time()
    reminders_collection.insert_one({
        "user": {
            "id": str(user_id),
            "email": email
        },
        "title": f"Review weak topic: {subject}",
        "time": reminder_time,
        "priority": "High",
        "auto": True,
        "notify_flags": {},
        "created_at": datetime.now(timezone.utc)
    })

    if email:
        subject_line = f"Study reminder created for {subject}"
        body = (
            f"Hello,\n\n"
            f"Based on a recent quiz result, a study reminder for \"{subject}\" has been scheduled for {reminder_time.strftime('%Y-%m-%d %H:%M UTC')}.\n\n"
            "Please review the topic to strengthen your understanding.\n\n"
            "— Smart Study Planner"
        )
        send_email(email, subject_line, body)

    return reminder_time


@quiz_bp.route('/submit', methods=['POST'])
def submit_quiz():
    # Get user_id from session (try both formats)
    user_id = None
    if 'user_id' in session:
        user_id = session['user_id']
    elif 'user' in session and isinstance(session['user'], dict) and session['user'].get('id'):
        user_id = session['user'].get('id')
    
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    data = request.get_json()
    subject = data.get('subject', 'General')
    score = data.get('score', 0)
    total = data.get('total', 1)
    correct = data.get('correct', 0)
    time_taken = data.get('time_taken', 0)

    # ✅ Save in DB with required fields
    today = datetime.now().date().isoformat()
    quiz_result = {
        "user_id": str(user_id),  # Store as string for consistency
        "subject": subject,
        "score": float(score),  # Percentage (0-100)
        "raw_score": correct,
        "total": total,
        "time_taken_seconds": time_taken,
        "date": today,
        "created_at": datetime.now(timezone.utc)
    }

    quizzes_collection.insert_one(quiz_result)

    # ✅ Update user's quiz stats and weak topics
    try:
        user_obj_id = ObjectId(user_id) if isinstance(user_id, str) else user_id

        # Get current user to calculate new average
        user = users_collection.find_one({'_id': user_obj_id})
        if user:
            current_quizzes_done = user.get('quizzes_done', 0)
            current_avg_score = user.get('average_score', 0)

            # Calculate new average
            new_total_quizzes = current_quizzes_done + 1
            new_avg_score = ((current_avg_score * current_quizzes_done) + float(score)) / new_total_quizzes

            update_payload = {
                'quizzes_done': new_total_quizzes,
                'average_score': round(new_avg_score, 2)
            }

            if float(score) < LOW_PERFORMANCE_THRESHOLD:
                update_payload.setdefault('weak_subjects', [])
                users_collection.update_one(
                    {'_id': user_obj_id},
                    {'$addToSet': {'weak_subjects': subject}}
                )

                user_email = session.get('user', {}).get('email')
                _create_weak_topic_task(user_id, subject)
                _create_auto_reminder(user_id, user_email, subject)

            users_collection.update_one(
                {'_id': user_obj_id},
                {'$set': update_payload}
            )
    except Exception as e:
        print(f"Error updating user stats: {str(e)}")

    # ✅ Auto log activity
    try:
        log_activity(str(user_id), "quiz_completed", {"subject": subject, "score": score})
    except Exception:
        pass

    return jsonify({"success": True, "message": "Quiz submitted successfully"})

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
