import requests
import smtplib
import json
import time
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Ticketmaster API settings
TICKETMASTER_API_KEY = os.getenv(
    "TICKETMASTER_API_KEY")  # Store in Replit Secrets
ARTIST_NAME = "Shania Twain"  # Change this to your preferred artist

# Mailgun SMTP settings
SMTP_SERVER = "smtp.mailgun.org"  # Mailgun's SMTP server
SMTP_PORT = 587
MAILGUN_USERNAME = os.getenv("MAILGUN_USERNAME")  # Store in Replit Secrets
MAILGUN_PASSWORD = os.getenv("MAILGUN_PASSWORD")  # Store in Replit Secrets
RECIPIENT_EMAIL = "tommipontinen76@proton.me"  # Change to your email
SENDER_EMAIL = "postmaster@sandbox85b8a0c8abe7430aadc1a129db3e6f45.mailgun.org"  # Mailgun-specified sender email

# File to store previous events
EVENTS_FILE = "events.json"


def fetch_events():
    """Fetch upcoming concerts for the specified artist from Ticketmaster."""
    url = f"https://app.ticketmaster.com/discovery/v2/events.json"
    params = {
        "apikey": TICKETMASTER_API_KEY,
        "keyword": ARTIST_NAME,
        "size": 10,
        "countryCode": "GB"  # Change if needed
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        if "_embedded" in data:
            return [{
                "id": event["id"],
                "name": event["name"],
                "venue": event["_embedded"]["venues"][0]["name"],
                "date": event["dates"]["start"]["localDate"],
                "url": event["url"]
            } for event in data["_embedded"]["events"]]
        print("No events found in response data")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error fetching events: {str(e)}")
        return []
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return []


def load_previous_events():
    """Load previously saved events from a JSON file."""
    try:
        with open(EVENTS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save_events(events):
    """Save the latest events to a JSON file."""
    with open(EVENTS_FILE, "w") as file:
        json.dump(events, file, indent=4)


def send_email_notification(event):
    """Send an email notification for a new event."""
    subject = f"New Concert: {event['name']}"
    body = (f"🎤 **New Concert Alert!** 🎤\n\n"
            f"**{event['name']}**\n"
            f"📍 Venue: {event['venue']}\n"
            f"📅 Date: {event['date']}\n"
            f"🔗 Tickets: {event['url']}")

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(MAILGUN_USERNAME, MAILGUN_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
        server.quit()
        print(f"✅ Email sent for {event['name']}")
    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")


def main():
    """Main function to check for new concerts and send notifications."""
    print("🎶 Ticketmaster Bot Running...")

    while True:
        print("🔎 Checking for new events...")
        new_events = fetch_events()
        previous_events = load_previous_events()

        new_event_ids = {event["id"] for event in new_events}
        previous_event_ids = {event["id"] for event in previous_events}

        new_events_to_notify = [
            event for event in new_events
            if event["id"] not in previous_event_ids
        ]

        if new_events_to_notify:
            print(f"🎉 Found {len(new_events_to_notify)} new event(s)!")
            for event in new_events_to_notify:
                send_email_notification(event)

            # Save updated events list
            save_events(new_events)
        else:
            print("🚫 No new events found.")

        print("⏳ Waiting 24 hours before checking again...")
        time.sleep(86400)  # Wait 24 hours before next check


if __name__ == "__main__":
    main()
