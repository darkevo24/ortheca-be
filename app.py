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
CORS(app)

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

    return jsonify(mailjet_response.json()), mailjet_response.status_code


# Endpoint to fetch events from Google Calendar
@app.route("/api/events", methods=["GET"])
def get_events():
    now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
    events_result = (
        service.events()
        .list(
            calendarId=CALENDAR_ID,
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])
    return jsonify({"events": events})


# Endpoint to add an event to Google Calendar
@app.route("/api/add-event", methods=["POST"])
def add_event():
    data = request.get_json()
    event = {
        "summary": data["title"],
        "start": {
            "dateTime": data["start"],
            "timeZone": "UTC",
        },
        "end": {
            "dateTime": data["end"],
            "timeZone": "UTC",
        },
    }
    service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    return jsonify({"message": "Event added successfully"})


if __name__ == "__main__":
    app.run(debug=True)
