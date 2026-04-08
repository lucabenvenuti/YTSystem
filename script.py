import os
import requests
import google.generativeai as genai
from mailjet_rest import Client
import sys
import re

# --- CONFIGURATION (2 Channels) ---
# Using the authentic UC IDs for maximum reliability
CHANNELS = {
    "Franchino Er Criminale": "UCi0pS-WsnV_m0tC99EqInEw",
    "Mr. RIP": "UCXpV8WIs0fAnu0TeHIhEq_Q"
}

def get_latest_video(channel_id):
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        response = requests.get(url)
        # Find the first video ID in the XML feed
        vid_ids = re.findall(r'<yt:videoId>(.*?)</yt:videoId>', response.text)
        return vid_ids[0] if vid_ids else None
    except Exception as e:
        print(f"Error fetching for {channel_id}: {e}")
        return None

if __name__ == "__main__":
    # Load Keys
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")
    MJ_KEY = os.getenv("MAILJET_API_KEY")
    MJ_SEC = os.getenv("MAILJET_SECRET_KEY")
    SENDER = os.getenv("SENDER_EMAIL")

    if not all([GEMINI_KEY, MJ_KEY, MJ_SEC, SENDER]):
        print("Error: Missing API Keys in GitHub Secrets.")
        sys.exit(1)

    # Init API
    genai.configure(api_key=GEMINI_KEY)
    gemini = genai.GenerativeModel('gemini-pro')
    mailjet = Client(auth=(MJ_KEY, MJ_SEC), version='v3.1')

    report_content = "<h2>Latest Updates</h2>"
    found_any = False

    for name, uc_id in CHANNELS.items():
        vid_id = get_latest_video(uc_id)
        if vid_id:
            found_any = True
            link = f"https://www.youtube.com/watch?v={vid_id}"
            
            # Simple Prompt for Gemini
            prompt = f"Summarize this YouTube video in 3 bullet points: {link}"
            try:
                response = gemini.generate_content(prompt)
                summary = response.text
            except:
                summary = "Could not generate summary."

            report_content += f"<h3>{name}</h3><p><a href='{link}'>Watch Video</a></p><p>{summary}</p><hr>"

    if found_any:
        data = {
          'Messages': [{
            "From": {"Email": SENDER, "Name": "YT Bot"},
            "To": [{"Email": "benvenutiluca@icloud.com", "Name": "Luca"}],
            "Subject": "6-Hour YouTube Intelligence Report",
            "HTMLPart": report_content
          }]
        }
        mailjet.send.create(data=data)
        print("Email sent successfully.")
    else:
        print("No videos found.")
