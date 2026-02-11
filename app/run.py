from dotenv import load_dotenv
import os
from app import create_app

# Load environment variables from .env file
load_dotenv()

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)



# from flask import Flask
# from config import Config
# from extensions.db import init_db

# # Import routes
# from routes import (
#     auth_routes,
#     planner_routes,
#     notes_routes,
#     quiz_routes,
#     suggestion_routes,
#     dashboard_routes,
#     motivation_routes
# )

# def create_app():
#     app = Flask(__name__)
#     app.config.from_object(Config)

#     # Initialize MongoDB
#     init_db(app)

#     # Register routes
#     app.register_blueprint(auth_routes.bp, url_prefix="/auth")
#     app.register_blueprint(planner_routes.bp, url_prefix="/planner")
#     app.register_blueprint(notes_routes.bp, url_prefix="/notes")
#     app.register_blueprint(quiz_routes.bp, url_prefix="/quiz")
#     app.register_blueprint(suggestion_routes.bp, url_prefix="/suggestions")
#     app.register_blueprint(dashboard_routes.bp, url_prefix="/dashboard")
#     app.register_blueprint(motivation_routes.bp, url_prefix="/motivation")

#     return app

# if __name__ == "__main__":
#     app = create_app()
#     app.run(debug=True)
