# from pymongo import MongoClient
# from flask_mail import Mail, Message
# from app.models import users_collection




# def model():

#     client=MongoClient("mongodb+srv://devanshn180_db_user:W7W9ZAApPjr5739@cluster0.njdxavv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
#     db=client("study_assistant")
#     return db

# def send_email(to_email,subject,body):
#     msg=Message(subject,recipient=[to_email])
#     msg.body=body
#     Mail.send(msg)
#     return send_email
    
from pymongo import MongoClient
import os

client = None
db = None

def init_extensions(app):
    global client, db
    
    # Configure MongoDB
    client = MongoClient("mongodb+srv://devanshn180_db_user:FkbFeDStf4-RK4G@cluster0.njdxavv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    db = client['study']   # Replace with your database name
