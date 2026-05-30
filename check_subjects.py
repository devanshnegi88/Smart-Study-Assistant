import os, sys
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://devanshn180_db_user:FkbFeDStf4-RK4G@cluster0.njdxavv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client["study"]

# Delete ALL quiz records (all are dummy test data with 0-20% scores)
r1 = db["quizzes"].delete_many({})
sys.stdout.write(f"Deleted {r1.deleted_count} quiz records\n")

# Clear subjects list from ALL user documents
r2 = db["users"].update_many({}, {"$set": {"subjects": []}})
sys.stdout.write(f"Cleared subjects from {r2.modified_count} users\n")

# Also clear any auto-created reminders from quiz low scores
r3 = db["reminders"].delete_many({"source": "quiz_low_score"})
sys.stdout.write(f"Deleted {r3.deleted_count} auto-quiz reminders\n")

sys.stdout.write("All clean!\n")
sys.stdout.flush()
