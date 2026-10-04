from flask import Flask, render_template, request, redirect, url_for
from google import genai
from googleapiclient.discovery import build
from dotenv import load_dotenv
from gmail_auth import get_gmail_credentials

import sqlite3
from datetime import datetime
import smtplib
from email.message import EmailMessage
import os
import time
import base64
import re


# =========================
# Environment
# =========================

load_dotenv()

app = Flask(__name__)

client = genai.Client()

DATABASE = "database.db"

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]


# =========================
# Database
# =========================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT,
            email TEXT,
            customer_message TEXT,
            ai_reply TEXT,
            status TEXT,
            created_at TEXT,
            gmail_message_id TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            company_name TEXT,
            response_language TEXT,
            response_tone TEXT,
            ai_instructions TEXT
        )
    """)

    existing_settings = cursor.execute(
        "SELECT * FROM settings WHERE id = 1"
    ).fetchone()

    if not existing_settings:

        cursor.execute("""
            INSERT INTO settings
            (
                id,
                company_name,
                response_language,
                response_tone,
                ai_instructions
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            1,
            "Customer Support",
            "English",
            "Professional and friendly",
            "Do not invent prices, policies, services, or information that was not provided."
        ))

    conn.commit()
    conn.close()


# =========================
# Settings
# =========================

def get_settings():

    conn = get_db_connection()

    settings = conn.execute(
        "SELECT * FROM settings WHERE id = 1"
    ).fetchone()

    conn.close()

    return settings


def save_settings(
    company_name,
    response_language,
    response_tone,
    ai_instructions
):

    conn = get_db_connection()

    conn.execute("""
        UPDATE settings
        SET
            company_name = ?,
            response_language = ?,
            response_tone = ?,
            ai_instructions = ?
        WHERE id = 1
    """, (
        company_name,
        response_language,
        response_tone,
        ai_instructions
    ))

    conn.commit()
    conn.close()


# =========================
# Send Email
# =========================

def send_email(customer_email, customer_name, reply_text):

    settings = get_settings()

    company_name = settings["company_name"]

    final_message = f"""Hello {customer_name},

{reply_text}

Best regards,
{company_name}
"""

    message = EmailMessage()

    message["Subject"] = "Reply to your request"
    message["From"] = EMAIL_ADDRESS
    message["To"] = customer_email

    message.set_content(final_message)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:

        server.starttls()

        server.login(
            EMAIL_ADDRESS,
            EMAIL_APP_PASSWORD
        )

        server.send_message(message)


# =========================
# Gmail Helpers
# =========================

def extract_email_address(sender):

    if not sender:
        return ""

    match = re.search(
        r'[\w\.-]+@[\w\.-]+\.\w+',
        sender
    )

    if match:
        return match.group(0)

    return sender


def extract_customer_name(sender):

    if not sender:
        return "Customer"

    match = re.match(
        r'^\s*(.*?)\s*<',
        sender
    )

    if match:

        name = match.group(1).strip()

        if name:
            return name

    email = extract_email_address(sender)

    if "@" in email:

        name = email.split("@")[0]

        name = name.replace(".", " ")
        name = name.replace("_", " ")

        return name.title()

    return "Customer"


def decode_gmail_data(data):

    if not data:
        return ""

    try:

        decoded = base64.urlsafe_b64decode(
            data + "=" * (-len(data) % 4)
        )

        return decoded.decode(
            "utf-8",
            errors="ignore"
        )

    except Exception:

        return ""


def get_email_body(payload):

    if not payload:
        return ""

    mime_type = payload.get("mimeType", "")

    body_data = payload.get(
        "body",
        {}
    ).get("data")

    if body_data and mime_type == "text/plain":

        return decode_gmail_data(body_data)

    parts = payload.get("parts", [])

    for part in parts:

        part_type = part.get("mimeType", "")

        if part_type == "text/plain":

            data = part.get(
                "body",
                {}
            ).get("data")

            if data:

                return decode_gmail_data(data)

    for part in parts:

        nested = get_email_body(part)

        if nested:

            return nested

    return ""


# =========================
# Check Gmail Connection
# =========================

def check_gmail_connection():

    try:

        credentials = get_gmail_credentials()

        service = build(
            "gmail",
            "v1",
            credentials=credentials
        )

        profile = service.users().getProfile(
            userId="me"
        ).execute()

        email_address = profile.get(
            "emailAddress",
            ""
        )

        return True, email_address

    except Exception as e:

        print("GMAIL CONNECTION ERROR:", e)

        return False, ""


# =========================
# Get Latest Gmail Email
# =========================

def get_latest_gmail_email():

    credentials = get_gmail_credentials()

    service = build(
        "gmail",
        "v1",
        credentials=credentials
    )

    result = service.users().messages().list(
        userId="me",
        q="in:inbox",
        maxResults=10
    ).execute()

    messages = result.get(
        "messages",
        []
    )

    if not messages:

        return None

    latest_message = messages[0]

    message_id = latest_message["id"]

    email_data = service.users().messages().get(
        userId="me",
        id=message_id,
        format="full"
    ).execute()

    payload = email_data.get(
        "payload",
        {}
    )

    headers = payload.get(
        "headers",
        []
    )

    sender = ""
    subject = ""

    for header in headers:

        name = header.get("name", "").lower()

        if name == "from":

            sender = header.get(
                "value",
                ""
            )

        elif name == "subject":

            subject = header.get(
                "value",
                ""
            )

    body = get_email_body(payload)

    return {
        "id": message_id,
        "sender": sender,
        "email": extract_email_address(sender),
        "customer": extract_customer_name(sender),
        "subject": subject,
        "body": body
    }


# =========================
# Gemini AI
# =========================

def generate_ai_reply(email):

    settings = get_settings()

    company_name = settings["company_name"]
    language = settings["response_language"]
    tone = settings["response_tone"]
    instructions = settings["ai_instructions"]

    prompt = f"""
You are an AI customer support assistant for {company_name}.

Customer name:
{email["customer"]}

Customer email:
{email["email"]}

Customer message:
{email["body"]}

Response language:
{language}

Response tone:
{tone}

Additional instructions:
{instructions}

Write a helpful and professional response to the customer.

IMPORTANT:
- Return ONLY the reply body.
- Do NOT include "Hello".
- Do NOT include the customer's name as a greeting.
- Do NOT include "Best regards".
- Do NOT include a signature.
- Do NOT invent prices, services, policies, or facts.
- If information is missing, politely ask the customer for clarification.
"""

    models = [
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash-lite",
        "gemini-flash-lite-latest",
        "gemini-3.5-flash"
    ]

    last_error = None

    for model_name in models:

        for attempt in range(2):

            try:

                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )

                text = response.text.strip()

                if text:

                    return text

            except Exception as e:

                last_error = e

                print(
                    f"Gemini error using {model_name}:",
                    e
                )

                time.sleep(2)

    raise Exception(
        f"Gemini could not generate a reply: {last_error}"
    )


# =========================
# Dashboard
# =========================

@app.route("/")
def home():

    conn = get_db_connection()

    requests_data = conn.execute("""
        SELECT *
        FROM requests
        ORDER BY id DESC
    """).fetchall()

    stats = {

        "new_requests": conn.execute("""
            SELECT COUNT(*)
            FROM requests
            WHERE status = 'Pending Approval'
        """).fetchone()[0],

        "pending_approval": conn.execute("""
            SELECT COUNT(*)
            FROM requests
            WHERE status = 'Pending Approval'
        """).fetchone()[0],

        "approved": conn.execute("""
            SELECT COUNT(*)
            FROM requests
            WHERE status = 'Approved'
        """).fetchone()[0]
    }

    conn.close()

    settings = get_settings()

    gmail_connected, gmail_email = check_gmail_connection()

    return render_template(
        "index.html",
        requests_data=requests_data,
        stats=stats,
        settings=settings,
        gmail_connected=gmail_connected,
        gmail_email=gmail_email
    )


# =========================
# Settings Page
# =========================

@app.route("/settings")
def settings_page():

    settings = get_settings()

    return render_template(
        "settings.html",
        settings=settings
    )


# =========================
# Save Settings
# =========================

@app.route(
    "/save-settings",
    methods=["POST"]
)
def save_settings_route():

    company_name = request.form.get(
        "company_name",
        "Customer Support"
    )

    response_language = request.form.get(
        "response_language",
        "English"
    )

    response_tone = request.form.get(
        "response_tone",
        "Professional and friendly"
    )

    ai_instructions = request.form.get(
        "ai_instructions",
        ""
    )

    save_settings(
        company_name,
        response_language,
        response_tone,
        ai_instructions
    )

    return redirect(
        url_for("settings_page")
    )


# =========================
# Check Gmail
# =========================

@app.route(
    "/check-gmail",
    methods=["POST"]
)
def check_gmail():

    try:

        email = get_latest_gmail_email()

        if not email:

            return redirect(
                url_for("home")
            )

        conn = get_db_connection()

        existing = conn.execute(
            """
            SELECT id
            FROM requests
            WHERE gmail_message_id = ?
            """,
            (email["id"],)
        ).fetchone()

        if existing:

            conn.close()

            return redirect(
                url_for("home")
            )

        ai_reply = generate_ai_reply(email)

        conn.execute("""
            INSERT INTO requests
            (
                customer,
                email,
                customer_message,
                ai_reply,
                status,
                created_at,
                gmail_message_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            email["customer"],
            email["email"],
            email["body"],
            ai_reply,
            "Pending Approval",
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            email["id"]
        ))

        conn.commit()
        conn.close()

    except Exception as e:

        print(
            "CHECK GMAIL ERROR:",
            e
        )

    return redirect(
        url_for("home")
    )


# =========================
# Manual Generate
# =========================

@app.route(
    "/generate",
    methods=["POST"]
)
def generate():

    customer_name = request.form.get(
        "customer_name",
        "Customer"
    )

    customer_email = request.form.get(
        "customer_email",
        ""
    )

    customer_message = request.form.get(
        "customer_message",
        ""
    )

    email_data = {

        "customer": customer_name,

        "email": customer_email,

        "body": customer_message
    }

    try:

        ai_reply = generate_ai_reply(
            email_data
        )

    except Exception as e:

        print(
            "GENERATE ERROR:",
            e
        )

        ai_reply = (
            "Sorry, we could not generate "
            "a reply at this time."
        )

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO requests
        (
            customer,
            email,
            customer_message,
            ai_reply,
            status,
            created_at,
            gmail_message_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        customer_name,
        customer_email,
        customer_message,
        ai_reply,
        "Pending Approval",
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        None
    ))

    conn.commit()
    conn.close()

    return redirect(
        url_for("home")
    )


# =========================
# Approve & Send
# =========================

@app.route(
    "/approve",
    methods=["POST"]
)
def approve():

    request_id = request.form.get(
        "request_id"
    )

    conn = get_db_connection()

    item = conn.execute(
        """
        SELECT *
        FROM requests
        WHERE id = ?
        """,
        (request_id,)
    ).fetchone()

    if not item:

        conn.close()

        return redirect(
            url_for("home")
        )

    try:

        send_email(
            item["email"],
            item["customer"],
            item["ai_reply"]
        )

        conn.execute("""
            UPDATE requests
            SET status = 'Approved'
            WHERE id = ?
        """, (
            request_id,
        ))

        conn.commit()

        print(
            "APPROVED REQUEST:",
            request_id
        )

    except Exception as e:

        print(
            "SEND EMAIL ERROR:",
            e
        )

    conn.close()

    return redirect(
        url_for("home")
    )


# =========================
# Reject
# =========================

@app.route(
    "/reject",
    methods=["POST"]
)
def reject():

    request_id = request.form.get(
        "request_id"
    )

    conn = get_db_connection()

    conn.execute("""
        UPDATE requests
        SET status = 'Rejected'
        WHERE id = ?
    """, (
        request_id,
    ))

    conn.commit()
    conn.close()

    return redirect(
        url_for("home")
    )


# =========================
# Edit Reply
# =========================

@app.route(
    "/edit",
    methods=["POST"]
)
def edit():

    request_id = request.form.get(
        "request_id"
    )

    edited_reply = request.form.get(
        "edited_reply",
        ""
    )

    conn = get_db_connection()

    conn.execute("""
        UPDATE requests
        SET ai_reply = ?
        WHERE id = ?
    """, (
        edited_reply,
        request_id
    ))

    conn.commit()
    conn.close()

    return redirect(
        url_for("home")
    )


# =========================
# Delete Request
# =========================

@app.route(
    "/delete",
    methods=["POST"]
)
def delete():

    request_id = request.form.get(
        "request_id"
    )

    conn = get_db_connection()

    conn.execute("""
        DELETE FROM requests
        WHERE id = ?
    """, (
        request_id,
    ))

    conn.commit()
    conn.close()

    return redirect(
        url_for("home")
    )


# =========================
# Start Application
# =========================


if __name__ == "__main__":
    init_database()
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )