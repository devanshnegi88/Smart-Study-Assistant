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
from flask_mail import Mail, Message
import os

client = None
db = None
mail = None

def init_extensions(app):
    global client, db, mail
    
    # Configure MongoDB
    client = MongoClient("mongodb+srv://devanshn180_db_user:FkbFeDStf4-RK4G@cluster0.njdxavv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    db = client['study']   # Replace with your database name
    
    # Configure Flask-Mail for Gmail
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USER', 'devanshnegi88@gmail.com')
    app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASSWORD', 'smle srpj twai myyb')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('EMAIL_USER', 'devanshnegi88@gmail.com')
    
    mail = Mail(app)

def send_email(to_email, subject, body):
    """Send email using Flask-Mail"""
    if not mail:
        return False
    try:
        msg = Message(subject, recipients=[to_email], body=body)
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
