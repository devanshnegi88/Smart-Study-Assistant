from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from app.models import users_collection  # Your MongoDB collection
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Login page
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = users_collection.find_one({'email': email})
        if user and check_password_hash(user.get('password', ''), password):
            # Store session with consistent format
            user_id_str = str(user['_id'])
            session['user_id'] = user_id_str
            session['user'] = {'id': user_id_str, 'email': email}
            flash("Login successful!", "success")
            return redirect(url_for('dashboard.dashboard'))  # redirect to dashboard
        else:
            flash("Invalid credentials. Please try again.", "error")
            return render_template("login.html")

    return render_template("login.html")

# Signup page
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')  # HTML input name="confirm_password"

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("signup.html")

        existing_user = users_collection.find_one({'email': email})
        if existing_user:
            flash("User already exists. Please login.", "error")
            return render_template("signup.html")

        # Hash password and insert
        hashed_password = generate_password_hash(password)
        result = users_collection.insert_one({
            'name': name,
            'email': email,
            'password': hashed_password,
            'study_time': {},
            'study_streak': 0,
            'quizzes_done': 0,
            'average_score': 0,
            'created_at': datetime.utcnow()
        })

        # Store session with user_id and user dict
        user_id_str = str(result.inserted_id)
        session['user_id'] = user_id_str
        session['user'] = {'id': user_id_str, 'email': email}
        
        flash("Signup successful! Choose how to set up your dashboard.", "success")
        return redirect(url_for('auth.option'))

    return render_template("signup.html")

# Option page after signup
@auth_bp.route('/option')
def option():
    if 'user' not in session:
        return redirect(url_for('auth.login'))
    return render_template("option.html")

# Forgot password page
@auth_bp.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        email = request.form.get('email')
        user = users_collection.find_one({'email': email})

        if user:
            flash(f"A reset link has been sent to {email}", "success")
        else:
            flash("Email not found. Please check again.", "error")

        return render_template("forgot.html")

    return render_template("forgot.html")

# Logout
@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user', None)
    flash("Logged out successfully!", "success")
    return redirect(url_for('auth.login'))