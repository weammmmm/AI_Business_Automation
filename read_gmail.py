from gmail_auth import get_gmail_credentials
from googleapiclient.discovery import build
import base64


def get_email_body(payload):

    # إذا كان الإيميل نصًا عاديًا
    if payload.get("body", {}).get("data"):

        data = payload["body"]["data"]

        return base64.urlsafe_b64decode(data).decode(
            "utf-8",
            errors="ignore"
        )

    # إذا كان الإيميل يحتوي على أجزاء متعددة
    parts = payload.get("parts", [])

    for part in parts:

        if part.get("mimeType") == "text/plain":

            data = part.get("body", {}).get("data")

            if data:

                return base64.urlsafe_b64decode(data).decode(
                    "utf-8",
                    errors="ignore"
                )

    return "No text body found."


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

        return

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

    print("\n==============================")
    print("LATEST EMAIL")
    print("==============================")

    print("From:", sender)

    print("Subject:", subject)

    print("\nMessage:")

    print(body)

    print("==============================\n")


if __name__ == "__main__":

    get_latest_email()