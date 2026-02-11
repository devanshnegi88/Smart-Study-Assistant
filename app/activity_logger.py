from datetime import datetime
from bson import ObjectId
from app.models import study_sessions_col, quizzes_collection

def log_activity(user_id, activity_type, metadata=None):
    """
    Automatically logs activity based on user actions.
    """
    metadata = metadata or {}
    today = datetime.now().date().isoformat()
    subject = metadata.get("subject", "General")

    if activity_type == "quiz_completed":
        quizzes_collection.insert_one({
            "user_id": ObjectId(user_id),
            "subject": subject,
            "score": metadata.get("score", 0),
            "date": today
        })

    elif activity_type == "chat_study" or activity_type == "notes_study":
        # check if today's session exists
        session = study_sessions_col.find_one({
            "user_id": ObjectId(user_id),
            "subject": subject,
            "date": today
        })

        if session:
            study_sessions_col.update_one(
                {"_id": session["_id"]},
                {"$inc": {
                    "duration": metadata.get("duration", 0.25),  # in hours
                    "topics_completed": metadata.get("topics_completed", 0)
                }}
            )
        else:
            study_sessions_col.insert_one({
                "user_id": ObjectId(user_id),
                "subject": subject,
                "duration": metadata.get("duration", 0.25),
                "topics_completed": metadata.get("topics_completed", 0),
                "total_topics": metadata.get("total_topics", 5),
                "date": today
            })
