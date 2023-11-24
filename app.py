import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import datetime
import requests
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load Google Calendar API credentials
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
SERVICE_ACCOUNT_FILE = "apt-bonbon-354106-57613de5dc3a.json"
CALENDAR_ID = "primary"

creds = None
if creds and creds.valid:
    service = build("calendar", "v3", credentials=creds)
else:
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("calendar", "v3", credentials=creds)


@app.route("/api/send-email", methods=["POST"])
def send_email():
    payload = request.json

    # Extract attachment content from the payload
    attachment_content = payload["Messages"][0]["Attachments"][0]["Content"]

    # Add the attachment content directly to the Mailjet payload
    payload["Messages"][0]["Attachments"][0]["Base64Content"] = attachment_content

    # Remove the original 'Content' key to avoid conflicts
    del payload["Messages"][0]["Attachments"][0]["Content"]

    mailjet_response = requests.post(
        "https://api.mailjet.com/v3.1/send",
        json=payload,
        headers={
            "Content-Type": "application/json",
        },
        auth=(
            os.getenv("MAILJET_API_KEY"),
            os.getenv("MAILJET_API_SECRET"),
        ),
    )

    print(mailjet_response.json())

    response = jsonify(mailjet_response.json())
    response.headers.add("Access-Control-Allow-Origin", "*")  # Allow all origins

    return response, mailjet_response.status_code


if __name__ == "__main__":
    app.run(debug=True)
