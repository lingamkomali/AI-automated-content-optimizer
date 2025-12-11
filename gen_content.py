import google.generativeai as genai
import pandas as pd
from slack_notify import send_slack_alert


GEMINI_API_KEY = "AIzaSyCFYZNzPbuTpPkiC3Dr8UKo7a0YXX_2t3U"  
genai.configure(api_key=GEMINI_API_KEY)

MODEL = "models/gemini-2.5-flash-preview-09-2025"

# CONTENT GENERATION

def generate_content(topic, platform):
    prompt = f"""
    You are a skilled AI content creator.
    Write engaging, concise, and high-quality content about "{topic}"
    suitable for the platform "{platform}".
    Make it interesting, platform-appropriate, and easy to read.
    Include 1–2 relevant hashtags only.
    """
    model = genai.GenerativeModel(MODEL)
    response = model.generate_content(prompt)
    return response.text.strip()

#saving this in csv

def save_to_csv(topic, platform, content, filename="generated_content1.csv"):
    df = pd.DataFrame([{
        "Topic": topic,
        "Platform": platform,
        "Generated_Content": content
    }])

    # Append data if file exists
    try:
        existing = pd.read_csv(filename)
        df = pd.concat([existing, df], ignore_index=True)
    except FileNotFoundError:
        pass

    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"\n Saved successfully to {filename}")

     # Send Slack notification after saving
    send_slack_alert(f" New content generated for *{topic}* on *{platform}*! File saved as `{filename}` ")

#main func

if __name__ == "__main__":
    topic = input("Enter a topic (e.g., AI marketing, AI in healthcare): ")
    platform = input("Enter platform (twitter / linkedin / youtube /reddit / google): ")

    print("\n Generating content...\n")
    content = generate_content(topic, platform)

    print(" Generated Content:\n")
    print(content)

    save_to_csv(topic, platform, content)
