from pymongo import MongoClient
import os

# Use environment variable or hardcoded fallback for development
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://devanshn180_db_user:FkbFeDStf4-RK4G@cluster0.njdxavv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

client = MongoClient(MONGO_URI)
db = client['study']

users_collection = db['users']
reminders_collection = db['reminders']
quizzes_collection = db['quizzes']
tasks_collection = db['tasks']
study_sessions_col = db['study_sessions']
progress_collection = db['progress']
form_collection = db['form']
