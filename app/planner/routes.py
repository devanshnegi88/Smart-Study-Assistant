from flask import Blueprint, jsonify, render_template, request, session
from app.models import users_collection, study_sessions_col, quizzes_collection, tasks_collection,reminders_collection
from bson.objectid import ObjectId
from datetime import datetime, timedelta

planner_bp = Blueprint('planner', __name__, url_prefix='/planner')

# -------------------------------------------------------------
# 📌 1. Compute AI Stats (AI Confidence, Learning Velocity, AI Subjects)
# -------------------------------------------------------------
def compute_stats(user_id):
    quizzes = list(quizzes_collection.find({'user_id': user_id}))

    if not quizzes:
        return {
            'ai_confidence': 0,
            'learning_velocity': '0x',
            'subjects': []
        }

    # Group scores by subject
    subject_scores = {}
    for q in quizzes:
        subject = q.get('subject', 'Unknown')
        score = q.get('score', 0)
        subject_scores.setdefault(subject, []).append(score)

    # Build subject averages
    subjects = []
    for sub, scores in subject_scores.items():
        avg = sum(scores) / len(scores)
        subjects.append({
            'subject': sub,
            'average_score': round(avg, 2),
            'count': len(scores)
        })

    # AI confidence (overall score)
    all_scores = [s for sublist in subject_scores.values() for s in sublist]
    ai_confidence = round(sum(all_scores) / len(all_scores), 0)

    # Compute learning velocity
    sessions = list(study_sessions_col.find({'user_id': user_id}))
    total_topics = sum(s.get('topics_completed', 0) for s in sessions)
    total_time = sum(s.get('duration', 0) for s in sessions) / 60

    velocity = round((total_topics / total_time), 2) if total_time > 0 else 0

    # AI Suggested subjects (weak subjects)
    suggested = []
    for s in subjects:
        if s['average_score'] < 60 or s['count'] < 3:
            suggested.append({
                "subject": s['subject'],
                "score": s['average_score'],
                "priority": (
                    "High" if s['average_score'] < 40 else
                    "Medium" if s['average_score'] < 70 else "Low"
                )
            })

    return {
        'ai_confidence': ai_confidence,
        'learning_velocity': f"{velocity}x",
        'subjects': suggested  # AI subjects only
    }


# -------------------------------------------------------------
# 📌 2. Auto Study Log Helper
# -------------------------------------------------------------
def log_study_activity(user_id, subject, duration=0, topics_completed=0, total_topics=0):
    today = datetime.now().date().isoformat()

    existing = study_sessions_col.find_one({
        "user_id": ObjectId(user_id),
        "subject": subject,
        "date": today
    })

    if existing:
        study_sessions_col.update_one(
            {"_id": existing["_id"]},
            {"$inc": {
                "duration": duration,
                "topics_completed": topics_completed,
                "total_topics": total_topics
            }}
        )
    else:
        study_sessions_col.insert_one({
            "user_id": ObjectId(user_id),
            "subject": subject,
            "duration": duration,
            "topics_completed": topics_completed,
            "total_topics": total_topics,
            "date": today
        })


# -------------------------------------------------------------
# 📌 3. Auto Track Time
# -------------------------------------------------------------
@planner_bp.route('/auto-time-log', methods=['POST'])
def auto_time_log():
    if 'user' not in session:
        return jsonify({"error": "User not logged in"}), 401

    seconds = float(request.json.get('seconds', 0))
    minutes = round(seconds / 60, 2)

    if minutes > 0:
        log_study_activity(session['user']['id'], "Active Study", duration=minutes)

    return jsonify({"success": True})


# -------------------------------------------------------------
# 📌 4. Chatbot Learning Log
# -------------------------------------------------------------
@planner_bp.route('/log-chat', methods=['POST'])
def log_chat_usage():
    if 'user' not in session:
        return jsonify({"error": "User not logged in"}), 401

    questions = int(request.json.get('questions', 1))
    user_id = session['user']['id']

    log_study_activity(user_id, "AI Chatbot", duration=1,
                       topics_completed=questions, total_topics=questions)

    return jsonify({"success": True})


# -------------------------------------------------------------
# 📌 5. Quiz Logging
# -------------------------------------------------------------
@planner_bp.route('/log-quiz', methods=['POST'])
def log_quiz_result():
    if 'user' not in session:
        return jsonify({"error": "User not logged in"}), 401

    user_id = session['user']['id']
    subject = request.json.get('subject')
    score = float(request.json.get('score', 0))
    today = datetime.now().date().isoformat()

    quizzes_collection.insert_one({
        "user_id": ObjectId(user_id),
        "subject": subject,
        "score": score,
        "date": today
    })

    log_study_activity(user_id, subject, duration=1, topics_completed=1, total_topics=1)

    return jsonify({"success": True})


# -------------------------------------------------------------
# 📌 6. Render Planner Page
# -------------------------------------------------------------
@planner_bp.route('/')
def planner_page():
    return render_template('planner.html')


# -------------------------------------------------------------
# 📌 7. Render Dashboard Page
# -------------------------------------------------------------
@planner_bp.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')


# -------------------------------------------------------------
# 📌 8. Dashboard API (Frontend uses this)
# -------------------------------------------------------------
@planner_bp.route('/dashboard-data')
def dashboard_data():
    if 'user' not in session:
        user_id = ObjectId("68ec90bf4699cec6b75a735e")
    else:
        user_id = ObjectId(session['user']['id'])

    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())

    # User
    user = users_collection.find_one({'_id': user_id})
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Study Sessions
    sessions = list(study_sessions_col.find({'user_id': user_id}))

    today_minutes = int(sum(s.get('duration', 0) for s in sessions if s.get('date') == today.isoformat()))

    weekly_progress = []
    for i in range(7):
        d = today - timedelta(days=6 - i)
        minutes = sum(s.get('duration', 0) for s in sessions if s.get('date') == d.isoformat())
        weekly_progress.append(round(minutes, 1))

    # Quizzes
    week_quizzes = list(quizzes_collection.find({
        'user_id': user_id,
        'date': {'$gte': week_start.isoformat()}
    }))
    quizzes_done = len(week_quizzes)
    avg_score = round(sum(q.get('score', 0) for q in week_quizzes) / quizzes_done, 0) if quizzes_done else 0

    # Streak
    streak = 0
    for i in range(7):
        d = today - timedelta(days=i)
        if any(s.get('date') == d.isoformat() and s.get('duration', 0) > 0 for s in sessions):
            streak += 1
        else:
            break

    # User Manually Added Subjects
    user_subjects = user.get('subjects', [])

    # Compute AI Stats
    stats = compute_stats(user_id)

    # Merge:
    # AI suggested subjects + User manual subjects
    all_subjects = stats['subjects'] + [
        {"subject": sub, "priority": "User Added", "score": "-"}
        for sub in user_subjects
    ]

    return jsonify({
        "studyTimeToday": today_minutes,
        "studyStreak": streak,
        "quizzesDone": quizzes_done,
        "averageScore": avg_score,
        "weeklyProgress": weekly_progress,
        "ai_confidence": stats['ai_confidence'],
        "learning_velocity": stats['learning_velocity'],
        "subjects": all_subjects
    })


# -------------------------------------------------------------
# 📌 Subject Details API for modal
# -------------------------------------------------------------
@planner_bp.route('/subject/<name>/details')
def subject_details(name):
    if 'user' not in session:
        return jsonify({"error": "User not logged in"}), 401

    user_id = ObjectId(session['user']['id'])
    today = datetime.now().date()

    # Recent quizzes for this subject (limit 10)
    recent_qs = list(quizzes_collection.find({
        'user_id': user_id,
        'subject': name
    }).sort('created_at', -1).limit(10))

    recent = []
    for q in recent_qs:
        recent.append({
            'date': q.get('date', q.get('created_at', '')).isoformat() if isinstance(q.get('created_at', ''), datetime) else q.get('date', q.get('created_at', '')),
            'score': q.get('score', 0)
        })

    # Today's study minutes for this subject
    today_record = study_sessions_col.find_one({
        'user_id': user_id,
        'subject': name,
        'date': today.isoformat()
    })
    today_minutes = round(today_record.get('duration', 0), 1) if today_record else 0

    # Weekly minutes per day for this subject
    weekly = []
    for i in range(7):
        d = today - timedelta(days=6 - i)
        minutes = sum(s.get('duration', 0) for s in study_sessions_col.find({'user_id': user_id, 'subject': name, 'date': d.isoformat()}))
        weekly.append(round(minutes, 1))

    # Average score & count for this subject
    all_scores = [q.get('score', 0) for q in list(quizzes_collection.find({'user_id': user_id, 'subject': name}))]
    count = len(all_scores)
    avg = round(sum(all_scores) / count, 1) if count else 0

    return jsonify({
        'subject': name,
        'recent_quizzes': recent,
        'today_minutes': today_minutes,
        'weekly_minutes': weekly,
        'average_score': avg,
        'quiz_count': count
    })


# -------------------------------------------------------------
# 📌 9. Add User Subject (Manual)
# -------------------------------------------------------------
@planner_bp.route('/add_subject', methods=['POST'])
def add_subject():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    subject = request.json.get("subject")
    if not subject:
        return jsonify({"error": "No subject provided"}), 400

    users_collection.update_one(
        {"_id": ObjectId(session['user']['id'])},
        {"$addToSet": {"subjects": subject}}
    )

    return jsonify({"success": True})


# -------------------------------------------------------------
# 📌 10. Delete Manually Added Subject ONLY (NOT AI SUBJECTS)
# -------------------------------------------------------------
@planner_bp.route('/delete_subject/<name>', methods=['DELETE'])
def delete_subject(name):
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    # Delete only from user.subjects (manual subjects)
    users_collection.update_one(
        {"_id": ObjectId(session['user']['id'])},
        {"$pull": {"subjects": name}}
    )

    return jsonify({"success": True})

@planner_bp.route('/add_reminder', methods=['POST'])
def add_reminder():
    if "user" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.json
    reminders_collection.insert_one({
        "user_id": ObjectId(session["user"]["id"]),
        "subject": data.get("subject"),
        "message": data.get("message"),
        "priority": data.get("priority", "Medium"),
        "auto": False,
        "created_at": datetime.now().isoformat()
    })

    return jsonify({"success": True})
