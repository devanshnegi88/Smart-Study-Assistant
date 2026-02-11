from flask import jsonify, Blueprint, render_template,session,request
from bson import ObjectId
from datetime import datetime, timedelta
from app.models import users_collection, tasks_collection, quizzes_collection, study_sessions_col, reminders_collection

dashboard_bp = Blueprint('dashboard', __name__,url_prefix='/api')


def compute_stats(user_id):
    # Convert ObjectId to string for querying
    user_id_str = str(user_id)
    
    # Quizzes
    quizzes = list(quizzes_collection.find({'user_id': user_id_str}))
    if not quizzes:
        return {'ai_confidence': 0, 'learning_velocity': '0x', 'subjects': []}

    # Group quizzes by subject
    subject_scores = {}
    for q in quizzes:
        subject = q.get('subject', 'Unknown')
        score = q.get('score', 0)
        subject_scores.setdefault(subject, []).append(score)

    subjects = []
    for sub, scores in subject_scores.items():
        avg = sum(scores) / len(scores)
        subjects.append({'subject': sub, 'average_score': round(avg, 2), 'count': len(scores)})

    # AI Confidence = overall average score
    all_scores = [s for sub in subject_scores.values() for s in sub]
    ai_confidence = round(sum(all_scores) / len(all_scores), 0)

    # Study Sessions → learning velocity
    sessions = list(study_sessions_col.find({'user_id': user_id_str}))
    total_topics = sum(s.get('topics_completed', 0) for s in sessions)
    total_time = sum(s.get('duration', 0) for s in sessions) / 60  # mins → hrs
    velocity = round((total_topics / total_time), 2) if total_time > 0 else 0

    # Suggest subjects where low score or few attempts
    suggested = [s for s in subjects if s['average_score'] < 60 or s['count'] < 3]

    return {
        'ai_confidence': ai_confidence,
        'learning_velocity': f"{velocity}x",
        'subjects': suggested
    }



@dashboard_bp.route('/')
def dashboard():
    return render_template('dashboard.html')

@dashboard_bp.route('/dashboard-data')
def dashboard_data():
    # Use your actual user ObjectId
    # user_id = ObjectId("68ec90bf4699cec6b75a735e")
    # ✅ Check login
    # Accept either session['user_id'] (preferred) or session['user']['id']
    user_id_str = None
    if 'user_id' in session:
        user_id_str = session['user_id']
    elif 'user' in session and isinstance(session['user'], dict) and session['user'].get('id'):
        user_id_str = session['user'].get('id')

    if not user_id_str:
        return jsonify({"error": "User not logged in"}), 401

    # ✅ Get ObjectId from session string
    try:
        user_id = ObjectId(user_id_str)
    except Exception:
        return jsonify({"error": "Invalid user id in session"}), 400

    # ✅ Fetch user
    user = users_collection.find_one({'_id': user_id})
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Dates as ISO strings
    today = datetime.now().date()
    today_str = today.isoformat()
    yesterday_str = (today - timedelta(days=1)).isoformat()

    # Study time today
    study_time_today = user.get('study_time', {}).get(today_str, 0)

    # Change from yesterday
    study_yesterday = user.get('study_time', {}).get(yesterday_str, 0)
    study_change = ((study_time_today - study_yesterday) / study_yesterday * 100) if study_yesterday else 100

    # Study streak
    study_streak = user.get('study_streak', 0)

    # Quizzes done this week
    week_start_str = (today - timedelta(days=today.weekday())).isoformat()
    quizzes_done = quizzes_collection.count_documents({
        'user_id': str(user_id),
        'date': {'$gte': week_start_str}
    })
    

    # Average score
    quiz_scores_cursor = quizzes_collection.find({'user_id': str(user_id)}, {'score': 1})
    quiz_scores = [q.get('score', 0) for q in quiz_scores_cursor]
    average_score = round(sum(quiz_scores) / len(quiz_scores), 0) if quiz_scores else 0

    # Weekly progress (last 7 days)
    weekly_progress = []
    for i in range(7):
        day_str = (today - timedelta(days=6-i)).isoformat()
        weekly_progress.append(user.get('study_time', {}).get(day_str, 0))

    # Upcoming tasks (next 5)
    upcoming_tasks_cursor = tasks_collection.find({
        'user_id': str(user_id),
        'date': {'$gte': today_str}
    }).sort('date', 1).limit(5)

    upcoming_tasks = []
    for t in upcoming_tasks_cursor:
        upcoming_tasks.append({
            'task': t.get('task_name', 'No Name'),
            'date': t.get('date', today_str),
            'priority': t.get('priority', 'low'),
            'type': 'task'
        })

    # Fetch reminders for this user (next 5)
    now = datetime.utcnow()
    user_session = session.get('user', {})
    user_email = user.get('email', '')  # Get email from the actual user document
    
    # Query reminders - they're stored with 'user' field containing the session user data
    reminders_cursor = reminders_collection.find({
        'time': {'$gte': now}
    }).sort('time', 1).limit(5)

    for r in reminders_cursor:
        # Check if this reminder belongs to the current user by email
        reminder_user = r.get('user', {})
        reminder_email = reminder_user.get('email', '')
        
        if reminder_email == user_email and user_email:
            reminder_date = r.get('time', now).strftime('%Y-%m-%d')
            reminder_time = r.get('time', now).strftime('%H:%M')
            upcoming_tasks.append({
                'task': r.get('title', 'No Title'),
                'date': reminder_date,
                'time': reminder_time,
                'priority': 'high',
                'type': 'reminder'
            })

    # Sort combined tasks and reminders by date
    upcoming_tasks = sorted(upcoming_tasks, key=lambda x: x.get('date', ''))

    stats = compute_stats(user_id)
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    user_subjects = user.get('subjects', [])
    all_subjects = stats['subjects'] + [{'subject': s, 'score': '-'} for s in user_subjects]

    return jsonify({
        'ai_confidence': stats['ai_confidence'],
        'learning_velocity': stats['learning_velocity'],
        'subjects': all_subjects,
        'studyTimeToday': study_time_today,
        'studyChange': round(study_change, 2),
        'studyStreak': study_streak,
        'quizzesDone': quizzes_done,
        'averageScore': average_score,
        'weeklyProgress': weekly_progress,
        'upcomingTasks': upcoming_tasks
    }) 

   

@dashboard_bp.route('/update-study-time', methods=['POST'])
def update_study_time():
    # Get user_id from session
    user_id_str = None
    if 'user_id' in session:
        user_id_str = session['user_id']
    elif 'user' in session and isinstance(session['user'], dict) and session['user'].get('id'):
        user_id_str = session['user'].get('id')
    
    if not user_id_str:
        return jsonify({"error": "User not logged in"}), 401
    
    data = request.get_json()
    seconds = data.get('seconds', 0)
    minutes = seconds // 60
    
    # Convert to ObjectId
    try:
        user_id = ObjectId(user_id_str)
    except:
        return jsonify({"error": "Invalid user id"}), 400
    
    # Get today's date as ISO string
    today_str = datetime.now().date().isoformat()
    
    # Update user's study_time for today
    users_collection.update_one(
        {'_id': user_id},
        {
            '$inc': {f'study_time.{today_str}': minutes},
            '$set': {'last_study_time': datetime.utcnow()}
        },
        upsert=False
    )
    
    return jsonify({"status": "success", "minutes_recorded": minutes})



# from flask import jsonify, Blueprint, render_template,session
# from bson import ObjectId
# from datetime import datetime, timedelta
# from app.models import users_collection, tasks_collection, quizzes_collection

# dashboard_bp = Blueprint('dashboard', __name__,url_prefix='/api')
# @dashboard_bp.route('/')
# def dashboard():
#     return render_template('dashboard.html')

# @dashboard_bp.route('/dashboard-data')
# def dashboard_data():
#     # Use your actual user ObjectId
    
#     if not session:
#         return jsonify({"error": "User not logged in"}), 401

#     user_id = session['id']

#     # ✅ Fetch user from MongoDB using ObjectId
#     user = users_collection.find_one({'_id': ObjectId(user_id)})
#     if not user:
#         return jsonify({"error": "User not found"}), 404

#     # Dates as ISO strings
#     today = datetime.now().date()
#     today_str = today.isoformat()
#     yesterday_str = (today - timedelta(days=1)).isoformat()

#     # Study time today
#     study_time_today = user.get('study_time', {}).get(today_str, 0)

#     # Change from yesterday
#     study_yesterday = user.get('study_time', {}).get(yesterday_str, 0)
#     study_change = ((study_time_today - study_yesterday) / study_yesterday * 100) if study_yesterday else 100

#     # Study streak
#     study_streak = user.get('study_streak', 0)

#     # Quizzes done this week
#     week_start_str = (today - timedelta(days=today.weekday())).isoformat()
#     quizzes_done = quizzes_collection.count_documents({
#     'user_id': str(user_id),
#     'date': {'$gte': week_start_str}
# })
    

#     # Average score
#     quiz_scores_cursor = quizzes_collection.find({'user_id': str(user_id)}, {'score': 1})
#     quiz_scores = [q.get('score', 0) for q in quiz_scores_cursor]
#     average_score = round(sum(quiz_scores) / len(quiz_scores), 2) if quiz_scores else 0

#     # Weekly progress (last 7 days)
#     weekly_progress = []
#     for i in range(7):
#         day_str = (today - timedelta(days=6-i)).isoformat()
#         weekly_progress.append(user.get('study_time', {}).get(day_str, 0))

#     # Upcoming tasks (next 5)
#     upcoming_tasks_cursor = tasks_collection.find({
#         'user_id': str(user_id),
#         'date': {'$gte': today_str}
#     }).sort('date', 1).limit(5)

#     upcoming_tasks = []
#     for t in upcoming_tasks_cursor:
#         upcoming_tasks.append({
#             'task': t.get('task_name', 'No Name'),
#             'date': t.get('date', today_str),
#             'priority': t.get('priority', 'low')
#         })

#     # Return JSON
#     return jsonify({
#         'studyTimeToday': study_time_today,
#         'studyChange': round(study_change, 2),
#         'studyStreak': study_streak,
#         'quizzesDone': quizzes_done,
#         'averageScore': average_score,
#         'weeklyProgress': weekly_progress,
#         'upcomingTasks': upcoming_tasks
#     })
