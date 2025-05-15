#!/usr/bin/env python3
"""
📧 emailer.py – Sends an email using Gmail SMTP

Usage:
  from emailer import send_email
  send_email("Subject", "Body text here")
"""

import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")

def send_email(subject, body):
    if not all([GMAIL_USER, GMAIL_PASS, EMAIL_TO]):
        raise ValueError("Missing email credentials in environment variables.")

    msg = EmailMessage()
    msg["From"] = GMAIL_USER
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_USER, GMAIL_PASS)
            smtp.send_message(msg)
        print(f"📬 Email sent: {subject}")
    except Exception as e:
        print(f"❌ Email failed: {e}")
