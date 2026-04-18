


from flask import Flask,session,render_template
from flask_mail import Mail
import os
from dotenv import load_dotenv

load_dotenv()
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your-secret-key'

    # Configure Flask-Mail from env vars or fallback defaults
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME", "devanshnegi88@gmail.com")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD", "smle srpj twai myyb")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER", "devanshnegi88@gmail.com")

    mail.init_app(app)
    

    # Initialize extensions
    from app.extensions import init_extensions
    init_extensions(app)

    # Register blueprints
    from app.auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    from app.chatbot import chatbot_bp
    app.register_blueprint(chatbot_bp)

    from app.dashboard.routes import dashboard_bp
    app.register_blueprint(dashboard_bp)

    from app.notes_sumariser.routes import notes_bp
    app.register_blueprint(notes_bp)

    from app.planner.routes import planner_bp
    app.register_blueprint(planner_bp)

    from app.progress.routes import progress_bp
    app.register_blueprint(progress_bp)

    from app.quizzes.routes import quiz_bp
    app.register_blueprint(quiz_bp)

    from app.reminders.routes import reminders_bp
    app.register_blueprint(reminders_bp)
    # NOTE: the reminder background thread is NOT started automatically.
    # To run daily reminder checks, start the scheduler manually by running
    # the scheduler script: `python -m app.reminder_email_scheduler`
    # or start the in-process thread from a Python shell:
    # >>> from app.reminders.routes import start_reminder_thread
    # >>> start_reminder_thread()

    from app.form.routes import preferences_bp
    app.register_blueprint(preferences_bp)

    from app.quizzes.assessment_routes import assessment_bp
    app.register_blueprint(assessment_bp)

    @app.route('/')
    
    def home():
        
            return render_template('home.html')




    return app


# This ensures create_app is available when importing 'app'
__all__ = ['create_app', 'mail']