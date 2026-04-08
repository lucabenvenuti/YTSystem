import os
import requests
import google.generativeai as genai
from mailjet_rest import Client
from datetime import datetime
import pytz
import json
import sys
import re

# --- 1. TIME GUARD ---
def should_run():
    tz = pytz.timezone("Europe/Berlin")
    now = datetime.now(tz)
    current_time = now.strftime("%H:%M")
    # Windows for 6:00, 13:30, 19:30
    targets = [("06:00", "06:40"), ("13:50", "14:30"), ("19:30", "20:10")]
    for start, end in targets:
        if start <= current_time <= end:
            return True, current_time
    return False, current_time

# --- 2. SEARCH LOGIC (No UC Codes Needed) ---
def get_latest_video(channel_name):
    try:
        # Search for the channel's most recent video
        search_url = f"https://www.youtube.com/results?search_query={channel_name}+latest&sp=CAI%253D"
        response = requests.get(search_url, headers={"User-Agent": "Mozilla/5.0"})
        # Extract the first video ID found in the HTML
        video_ids = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", response.text)
        return video_ids[0] if video_ids else None
    except Exception as e:
        print(f"Search failed for {channel_name}: {e}")
        return None

# --- 3. CHANNEL LIST (All 77) ---
CHANNELS = [
    "Franchino Er Criminale", "Frank", "Il signor Franz", "Mochohf", 
    "Francesco Costa", "cavernadiplatone", "The Babylon Bee", 
    "Pirate Software", "motivationaldoc", "Screen Junkies", "The Ramsey Show Highlights", 
    "RaiNews", "Dwarkesh Patel", "John Barrows", "Daniel Greene", "Max Klymenko", 
    "Polimi", "SandRhoman History", "Illumina Show", "HistoryMarche", 
    "What are we eating today?", "The Desirable Truth", "Francesco Zini", 
    "GialloZafferano", "Fatto in Casa da Benedetta", "Silvi's Little World", 
    "Working Dog Productions", "Proactive Thinker", "Danilo Toninelli", 
    "Principles by Ray Dalio", "Practical Wisdom", "Jeremy London, MD", 
    "iStorica", "VisualPolitik EN", "Domus Orobica", "Graham Stephan", 
    "Harry Potter Theory", "The Economist", "Shark Tank Global", "Alux.com", 
    "Chris Galbiati", "Le Coliche", "ViviGermania", "Casa Pappagallo", 
    "Abandoned Films", "Cucina con Ruben", "Paul Chadeisson", "TED-Ed", "TED", 
    "VICE News", "Ian Koniak", "Sous Vide Everything", "More Perfect Union", 
    "Adult Swim", "Big Think", "Graham Cochrane", "Kings and Generals", 
    "freeCodeCamp.org", "Reynard Lowell", "Real Men Real Style", "Sven Carlin", 
    "Maurizio Merluzzo", "Vassalli di Barbero", "xMurry", "Pietro Morello", 
    "ThePrimeCronus", "GermanPod101", "CareerVidz", "Viva La Dirt League", 
    "LegalEagle", "DUST", "Imperial Iterator", "Comedy Kick", "Scripta Manent", 
    "A Life After Layoff", "Dr. Ana", "Mr. RIP"
]

if __name__ == "__main__":
    is_time, german_now = should_run()
    if not is_time:
        print(f"Current German time {german_now}. Skipping.")
        sys.exit(0)

    # Load Secrets
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")
    MJ_KEY = os.getenv("MAILJET_API_KEY")
    MJ_SEC = os.getenv("MAILJET_SECRET_KEY")
    SENDER = os.getenv("SENDER_EMAIL")

    if not all([GEMINI_KEY, MJ_KEY, MJ_SEC, SENDER]):
        print("Error: Missing environment variables.")
        sys.exit(1)

    # Initialize Clients
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-pro')
    mailjet = Client(auth=(MJ_KEY, MJ_SEC), version='v3.1')

    # Main Loop
    final_report = ""
    for channel in CHANNELS:
        vid_id = get_latest_video(channel)
        if vid_id:
            # Here you would add your summary logic
            final_report += f"**{channel}**: https://youtube.com/watch?v={vid_id}\n"

    # Send Email (Simplified example)
    data = {
      'Messages': [{
        "From": {"Email": SENDER, "Name": "YT Bot"},
        "To": [{"Email": "benvenutiluca@icloud.com", "Name": "Luca"}],
        "Subject": f"YT Intelligence - {german_now}",
        "TextPart": final_report
      }]
    }
    mailjet.send.create(data=data)
    print("Done!")
