# slack_notify.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def send_slack_alert(message):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    print(f"Loaded Slack webhook: {webhook_url}")

    payload = {"text": message}
    response = requests.post(webhook_url, json=payload)

    if response.status_code == 200:
        print("✅ Sent Slack alert successfully")
    else:
        print(f"❌ Failed to send Slack message: {response.text}")

# 🔽 Add this block at the end
if __name__ == "__main__":
    send_slack_alert("🚀 Test notification: Slack alerts working successfully!")
