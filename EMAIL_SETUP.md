# Email Setup Guide for Password Reset

## Prerequisites
Flask-Mail is already installed. Now you need to configure Gmail to send emails.

## Step 1: Enable 2FA on Gmail
1. Go to https://myaccount.google.com
2. Click "Security" in the left menu
3. Enable "2-Step Verification" (if not already enabled)

## Step 2: Generate Gmail App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer" (or your device)
3. Google will generate a 16-character password
4. Copy this password (you'll need it in the next step)

## Step 3: Set Environment Variables in PowerShell

Replace `your-email@gmail.com` with your Gmail address and `your-app-password` with the 16-character password from Step 2.

```powershell
# In PowerShell, run these commands:
$env:EMAIL_USER = "your-email@gmail.com"
$env:EMAIL_PASSWORD = "your-app-password"

# Verify they're set:
echo $env:EMAIL_USER
echo $env:EMAIL_PASSWORD
```

## Step 4: Run Your Flask App

```powershell
python app1.py
```

## Step 5: Test the Forgot Password Feature

1. Go to http://localhost:5000/auth/forgot
2. Enter an email address registered in your system
3. Check your Gmail inbox for the reset link
4. Click the link to reset your password

## Troubleshooting

- **"SMTP Authentication Error"**: Check that your app password is correct (it should be 16 characters with spaces)
- **"Less secure app access denied"**: Make sure you used an "App Password", not your regular Gmail password
- **"Connection refused"**: Ensure your internet connection is working and Gmail SMTP is accessible

## Example Email Configuration

The email will be sent from: `your-email@gmail.com`
Subject: `Password Reset Request - Smart Study Assistant`

The reset link expires in 30 minutes.
