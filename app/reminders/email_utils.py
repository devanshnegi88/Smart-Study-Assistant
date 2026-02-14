# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# import os

# EMAIL_USER = os.getenv("MAIL_USERNAME")
# EMAIL_PASS = os.getenv("MAIL_PASSWORD")

# def send_email(to_email, subject, body):
#     msg = MIMEMultipart()
#     msg["From"] = EMAIL_USER
#     msg["To"] = to_email
#     msg["Subject"] = subject

#     msg.attach(MIMEText(body, "plain"))

#     try:
#         server = smtplib.SMTP("smtp.gmail.com", 587)
#         server.starttls()
#         server.login(EMAIL_USER, EMAIL_PASS)
#         server.sendmail(EMAIL_USER, to_email, msg.as_string())
#         server.quit()
#         print(f"[EMAIL SENT] {to_email} -> {subject}")
#         return True

#     except Exception as e:
#         print("[EMAIL FAILED]", e)
#         return False
