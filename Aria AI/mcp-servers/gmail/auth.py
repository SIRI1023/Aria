"""Run this once to authorize Gmail access and save token.json."""
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "..", "google-calendar", "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")


def main():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    print("Auth successful! token.json saved.")

    # Quick test — list 3 emails to confirm it works
    service = build("gmail", "v1", credentials=creds)
    result = service.users().messages().list(userId="me", maxResults=3).execute()
    messages = result.get("messages", [])
    print(f"Connected to Gmail — {len(messages)} messages found in inbox.")
    print("You can now restart the backend and ask Aria about your emails.")


if __name__ == "__main__":
    main()
