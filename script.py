import os
import requests
import google.genai as genai
import re
import time
import random
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi

# --- CONFIGURATION ---
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
    "Wizards and Warriors": "UCwqY9GjXBdSYeUZiinbFXyQ",
    "Mocho": "UC1Qm-YEYyAAQYXgI_vsIqCw",
    "Dami Lee": "UCJ_2hNMxOzNjviJBiLWHMqg",
    "Economics Explained": "UCZ4AMrDcNrfy3X6nsU8-rPg",
    "How Money Works": "UCkCGANrihzExmu9QiqZpPlQ",
    "Iron Snail": "UC-0kjvCj9Z_pL_yH648Uq7w",
    "Signor Franz": "UCLpGbBGYr9yCGbSwDEFvrMQ",
    "Francesco Costa": "UCWIkgZzXznmBgU9uQsvjZAQ",
    "Lost le Blanc": "UCt_NLJ4McJlCyYM-dSPRo7Q"
}

def get_latest_vid(channel_id):
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        r = requests.get(url, timeout=10)
        vids = re.findall(r'<yt:videoId>(.*?)</yt:videoId>', r.text)
        titles = re.findall(r'<title>(.*?)</title>', r.text)
        return (vids[0], titles[1]) if vids else (None, None)
    except Exception as e:
        print(f"DEBUG: RSS Fetch failed for {channel_id}: {e}")
        return (None, None)

def get_transcript(video_id):
    # 1. DEBUG: Verify Secret Loading
    cookies_content = os.getenv("YOUTUBE_COOKIES")
    if not cookies_content:
        print("CRITICAL: YOUTUBE_COOKIES Secret is MISSING from Env!")
        return None
    
    with open("cookies.txt", "w") as f:
        f.write(cookies_content)
    
    c_size = os.path.getsize("cookies.txt")
    print(f"DEBUG: Cookies.txt size: {c_size} bytes")

    try:
        # 2. HUMAN JITTER
        delay = random.uniform(12, 22)
        print(f"DEBUG: Waiting {delay:.1f}s for {video_id}...")
        time.sleep(delay)
        
        # 3. ATTEMPT FETCH
        tl = YouTubeTranscriptApi.list_transcripts(video_id, cookies="cookies.txt")
        
        try:
            t = tl.find_transcript(['it', 'en'])
            print(f"SUCCESS: Found MANUAL transcript for {video_id}")
        except:
            t = tl.find_generated_transcript(['it', 'en'])
            print(f"SUCCESS: Found AUTO transcript for {video_id}")

        full_text = " ".join([snippet['text'] for snippet in t.fetch()])
        print(f"DEBUG: Captured {len(full_text)} characters.")
        return full_text[:15000]

    except Exception as e:
        print(f"FAIL: YouTube Block for {video_id}. Error: {type(e).__name__}")
        return None

if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    rss_items = ""

    for name, cid in CHANNELS.items():
        vid, v_title = get_latest_vid(cid)
        if vid:
            url = f"https://www.youtube.com/watch?v={vid}"
            print(f"\n--- Processing: {name} ---")

            transcript_text = get_transcript(vid)
            label = "TRANSCRIPT" if transcript_text else "TITLE-ONLY"

            try:
                source = f"Transcript: {transcript_text}" if transcript_text else f"Title: {v_title}"
                
                # --- GEMINI 3.1 FLASH-LITE PREVIEW ---
                response = client.models.generate_content(
                    model="gemini-3.1-flash-lite-preview", 
                    contents=(
                        f"Start with **{label}**.\n\n"
                        f"Video: '{v_title}'\n"
                        f"Content: {source}\n\n"
                        "Task: Summarize in 5 bullet points. Match the language of the content."
                    )
                )
                
                if response.text:
                    print(f"DEBUG: Gemini successfully generated summary.")
                    summary = response.text.strip().replace("\n", "<br>")
                else:
                    summary = f"**{label}**<br>Gemini returned no text."

            except Exception as e:
                print(f"GEMINI ERROR for {name}: {e}")
                summary = f"**{label}**<br>Summary failed: {type(e).__name__}"

            rss_items += f"""
            <item>
                <title>{name}: {v_title}</title>
                <link>{url}</link>
                <description><![CDATA[{summary}]]></description>
                <pubDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
                <guid isPermaLink="false">{vid}-{int(time.time())}</guid>
            </item>"""
            
            time.sleep(5)

    rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0">
    <channel>
        <title>YouTube Intelligence AI</title>
        <link>https://github.com/lucabenvenuti/ytTranscripts</link>
        <description>Daily AI Video Summaries</description>
        {rss_items}
    </channel>
    </rss>"""

    with open("feed.xml", "w", encoding="utf-8") as f:
        f.write(rss_feed)

    print("\nFINISH: feed.xml updated.")
