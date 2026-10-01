from gmail_auth import get_gmail_credentials
from googleapiclient.discovery import build
from google import genai
from dotenv import load_dotenv
import base64
import os


load_dotenv()

client = genai.Client()


def get_email_body(payload):

    if payload.get("body", {}).get("data"):

        data = payload["body"]["data"]

        return base64.urlsafe_b64decode(data).decode(
            "utf-8",
            errors="ignore"
        )

    for part in payload.get("parts", []):

        if part.get("mimeType") == "text/plain":

            data = part.get("body", {}).get("data")

            if data:

                return base64.urlsafe_b64decode(data).decode(
                    "utf-8",
                    errors="ignore"
                )

    return ""


def get_latest_email():

    credentials = get_gmail_credentials()

    service = build(
        "gmail",
        "v1",
        credentials=credentials
    )

    results = service.users().messages().list(
        userId="me",
        maxResults=1
    ).execute()

    messages = results.get("messages", [])

    if not messages:

        print("No emails found.")

        return None

    message_id = messages[0]["id"]

    message = service.users().messages().get(
        userId="me",
        id=message_id,
        format="full"
    ).execute()

    headers = message["payload"].get("headers", [])

    sender = ""
    subject = ""

    for header in headers:

        if header["name"].lower() == "from":
            sender = header["value"]

        if header["name"].lower() == "subject":
            subject = header["value"]

    body = get_email_body(
        message["payload"]
    )

    return {
        "sender": sender,
        "subject": subject,
        "body": body
    }


def generate_ai_reply(email):

    prompt = f"""
You are a professional customer service assistant.

Read the customer's email and write a friendly,
clear and concise business reply.

Important:
- Do not invent prices.
- Do not invent company policies.
- Do not invent information that was not provided.
- Reply directly to the customer's message.
- Keep the reply professional and helpful.
- Keep it reasonably short.

Customer email:
{email["sender"]}

Subject:
{email["subject"]}

Message:
{email["body"]}
"""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )

    return response.text.strip()


if __name__ == "__main__":

    print("\nReading latest Gmail message...")

    email = get_latest_email()

    if email:

        print("\n==============================")
        print("CUSTOMER EMAIL")
        print("==============================")

        print("From:", email["sender"])
        print("Subject:", email["subject"])

        print("\nGenerating AI reply...")

        ai_reply = generate_ai_reply(email)

        print("\n==============================")
        print("AI REPLY")
        print("==============================")

        print(ai_reply)

        print("==============================")