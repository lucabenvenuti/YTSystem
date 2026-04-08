import os
import feedparser
import json
import smtplib
from email.message import EmailMessage
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai

# --- CONFIG ---
CHANNELS = {
    "Franchino Er Criminale": "UC_x5XG1OV2P6uYZ5FHSWvAw",
    "Will Media": "UCvY6f9m5HId4XU_RCHtKjFw"
}
DB_FILE = "processed_videos.json"

# Setup AI
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

def send_email(subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = os.environ["SENDER_EMAIL"]
    msg['To'] = "benvenutiluca@icloud.com"

    # Mailjet SMTP Config
    with smtplib.SMTP("in-v3.mailjet.com", 587) as server:
        server.starttls()
        server.login(os.environ["MAILJET_API_KEY"], os.environ["MAILJET_SECRET_KEY"])
        server.send_message(msg)

def get_summary(title, text):
    prompt = f"Summarize this YouTube transcript for '{title}'. Use a 'Too Long; Didn't Watch' intro, then 5 bullet points. Language: Italian. \n\nTranscript: {text}"
    response = model.generate_content(prompt)
    return response.text

# Load database
if os.path.exists(DB_FILE):
    with open(DB_FILE, 'r') as f:
        processed = json.load(f)
else:
    processed = []

new_processed = list(processed)

for name, cid in CHANNELS.items():
    feed = feedparser.parse(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}")
    for entry in feed.entries[:2]: # Check 2 most recent
        v_id = entry.yt_videoid
        if v_id not in processed:
            try:
                # Try fetching Italian or English transcript
                t_list = YouTubeTranscriptApi.get_transcript(v_id, languages=['it', 'en'])
                text = " ".join([i['text'] for i in t_list])
                
                summary = get_summary(entry.title, text)
                
                send_email(f"Riassunto: {entry.title}", f"Canale: {name}\nLink: {entry.link}\n\n{summary}")
                new_processed.append(v_id)
                print(f"Success: {entry.title}")
            except Exception as e:
                print(f"Skipping {entry.title}: {e}")

# Save database
with open(DB_FILE, 'w') as f:
    json.dump(new_processed, f)
