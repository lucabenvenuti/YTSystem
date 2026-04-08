import os
import requests
import google.generativeai as genai
from mailjet_rest import Client
import re
import sys

# THE 2 ORIGINAL CHANNELS
CHANNELS = {
    "Franchino Er Criminale": "UCi0pS-WsnV_m0tC99EqInEw",
    "Mr. RIP": "UCXpV8WIs0fAnu0TeHIhEq_Q"
}

def get_latest_vid(channel_id):
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        r = requests.get(url, timeout=10)
        vids = re.findall(r'<yt:videoId>(.*?)</yt:videoId>', r.text)
        return vids[0] if vids else None
    except:
        return None

if __name__ == "__main__":
    # 1. Setup
    api_key = os.getenv("GEMINI_API_KEY")
    mj_key = os.getenv("MAILJET_API_KEY")
    mj_sec = os.getenv("MAILJET_SECRET_KEY")
    sender = os.getenv("SENDER_EMAIL")

    if not all([api_key, mj_key, mj_sec, sender]):
        print("Error: Missing Secrets")
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash') # Using Flash for speed
    mailjet = Client(auth=(mj_key, mj_sec), version='v3.1')

    # 2. Logic
    html_body = "<h1>Latest Summaries</h1>"
    
    for name, cid in CHANNELS.items():
        vid = get_latest_vid(cid)
        if vid:
            url = f"https://www.youtube.com/watch?v={vid}"
            prompt = f"Summarize this video in 3 punchy bullet points: {url}"
            try:
                res = model.generate_content(prompt)
                summary = res.text
            except:
                summary = "Summary unavailable."
            
            html_body += f"<h3>{name}</h3><p><a href='{url}'>Watch</a></p><p>{summary}</p><hr>"

    # 3. Send
    data = {
      'Messages': [{
        "From": {"Email": sender, "Name": "YT Bot"},
        "To": [{"Email": "benvenutiluca@icloud.com"}],
        "Subject": "YT Update (6-Hour Interval)",
        "HTMLPart": html_body
      }]
    }
    mailjet.send.create(data=data)
    print("Success!")
