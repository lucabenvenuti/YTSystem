import os
import requests
import google.generativeai as genai
from mailjet_rest import Client
import re
import sys

# --- CONFIGURATION (2 Original + 10 New Verified) ---
CHANNELS = {
    "Franchino Er Criminale": "UCi0pS-WsnV_m0tC99EqInEw",
    "Mr. RIP": "UCXpV8WIs0fAnu0TeHIhEq_Q",
    "SandRhoman History": "UC7pr_dQxm2Ns2KlzRSx5FZA",
    "Illumina Show": "UCYhJxmRknd1gLZa1dxjm4Hw",
    "HistoryMarche": "UC8MX9ECowgDMTOnFTE8EUJw",
    "What are we eating today?": "UCuApobilcYeWdlbhdp746RA",
    "Kings and Generals": "UCMmaBzfCCwZ2KqaBJjkj0fw",
    "Chris Galbiati": "UClvlYh79P6GKOzgfgISrBHg",
    "Francesco Zini": "UCiGp4I5ehgrCF8cKlXvvX2w",
    "Frank Vlog": "UC9w_-HRrQwkyWlbI2mTedxQ",
    "Giulia Crossbow": "UCLYbP4QpYiwcnIqm_cgAtJg",
    "Wizards and Warriors": "UCwqY9GjXBdSYeUZiinbFXyQ"
}

def get_latest_vid(channel_id):
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        r = requests.get(url, timeout=15)
        # Regex to pull the most recent video ID from the RSS feed
        vids = re.findall(r'<yt:videoId>(.*?)</yt:videoId>', r.text)
        return vids[0] if vids else None
    except Exception as e:
        print(f"Error fetching {channel_id}: {e}")
        return None

if __name__ == "__main__":
    # 1. API Setup
    api_key = os.getenv("GEMINI_API_KEY")
    mj_key = os.getenv("MAILJET_API_KEY")
    mj_sec = os.getenv("MAILJET_SECRET_KEY")
    sender = os.getenv("SENDER_EMAIL")

    if not all([api_key, mj_key, mj_sec, sender]):
        print("Error: Missing GitHub Secrets")
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    mailjet = Client(auth=(mj_key, mj_sec), version='v3.1')

    # 2. Logic
    html_body = "<h1>YouTube Intelligence: Latest Summaries</h1><hr>"
    found_any = False
    
    for name, cid in CHANNELS.items():
        vid = get_latest_vid(cid)
        if vid:
            found_any = True
            url = f"https://www.youtube.com/watch?v={vid}"
            # Prompting Gemini to provide a concise summary
            prompt = f"Summarize this video in 3 punchy bullet points: {url}"
            
            try:
                res = model.generate_content(prompt)
                summary = res.text
            except:
                summary = "Summary unavailable for this video."
            
            html_body += f"<h3>{name}</h3><p><a href='{url}'>Watch Video</a></p><p>{summary}</p><hr>"

    # 3. Email Dispatch
    if found_any:
        data = {
          'Messages': [{
            "From": {"Email": sender, "Name": "YT Bot"},
            "To": [{"Email": "benvenutiluca@icloud.com"}],
            "Subject": "YouTube Intelligence Report (Updated Channel List)",
            "HTMLPart": html_body
          }]
        }
        mailjet.send.create(data=data)
        print("Success: Email dispatched.")
    else:
        print("No new videos found.")
