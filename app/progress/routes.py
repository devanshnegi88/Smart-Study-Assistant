from flask import Flask,Blueprint,session,redirect,url_for,request,jsonify,render_template
# from .import progress_bp
from app.models import progress_collection

progress_bp=Blueprint("progress",__name__, url_prefix='/progress')
@progress_bp.route('/set',methods=['GET','POST'])

def set_goal():
    if "email" not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        
        goal=request.json.get('goal')

        progress_collection.update_one(
            {'email':session['email']},
            {'$set':{goal:goal}}
        )
        return jsonify({'goal':goal})


@progress_bp.route('study_log',methods=['POST'])
def study_logs():
    if "email" not in session:
        return redirect(url_for('auth.login'))
    
    day=request.json.get('day')
    minutes=request.json.get('minutes')

    progress_collection.update_one(
        {'email':session['email']},
        {'$set':{'day':day,'minutes':minutes}}
    )
    return jsonify({'day':day,'minutes':minutes})


@progress_bp.route('/weekly_data',methods=['GET'])

def weekly_data():
    if "email" not in session:
        return redirect(url_for('auth.login'))
    
    email=session['email']
    
    logs=progress_collection.find_one({'email':session['email']})
    weekly_data={}
    for log in logs:
        weekly_data[log['day']]=log['minutes']

    return jsonify({'weekly_data':weekly_data})  




@progress_bp.route('/progress',methods=['GET'])
def progress():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    
    return render_template('progress.html')

@progress_bp.route('/ai-insights', methods=['GET'])
def ai_insights():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    return jsonify({"error": "AI insights temporarily disabled."}), 503