


from flask import Flask,session,render_template

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your-secret-key'

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

    from app.form.routes import preferences_bp
    app.register_blueprint(preferences_bp)

    from app.quizzes.assessment_routes import assessment_bp
    app.register_blueprint(assessment_bp)

    @app.route('/')
    
    def home():
        
            return render_template('home.html')




    return app


# This ensures create_app is available when importing 'app'
__all__ = ['create_app']