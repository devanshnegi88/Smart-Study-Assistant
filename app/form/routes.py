from flask import Blueprint, render_template, request, jsonify, session
from app.models import form_collection

preferences_bp = Blueprint('preferences', __name__)

# GET route for loading the page
@preferences_bp.route("/preferences", methods=["GET"])
def show_preferences():
    return render_template("option.html")

# POST route for saving preferences
@preferences_bp.route("/preferences", methods=["POST"])
def save_preferences():
    data = request.get_json()
    print("✅ Received data:", data)  # Debugging log

    if not data:
        return jsonify({"success": False, "message": "No data received"}), 400

    # Extract fields from data
    full_name = data.get("fullName")
    education_level = data.get("educationLevel")
    current_year = data.get("currentYear")
    subjects = data.get("subjects", [])
    exam_goal = data.get("examGoal")
    study_days = data.get("studyDays", [])
    start_time = data.get("startTime")
    end_time = data.get("endTime")
    study_duration = data.get("studyDuration")
    break_preference = data.get("breakPreference")
    ai_focus = data.get("aiPlanFocus")
    auto_adjust = data.get("autoAdjust", False)

    # Insert into MongoDB
    result = form_collection.insert_one({
        "fullName": full_name,
        "educationLevel": education_level,
        "currentYear": current_year,
        "subjects": subjects,
        "examGoal": exam_goal,
        "studyDays": study_days,
        "startTime": start_time,
        "endTime": end_time,
        "studyDuration": study_duration,
        "breakPreference": break_preference,
        "aiPlanFocus": ai_focus,
        "autoAdjust": auto_adjust
    })

    print("🟢 Inserted document ID:", result.inserted_id)

    return jsonify({"success": True, "message": "Preferences saved successfully!"})