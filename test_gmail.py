from gmail_auth import get_gmail_credentials

print("Starting Gmail authentication...")

credentials = get_gmail_credentials()

print("Gmail authentication successful!")
print("Credentials saved in token.json")