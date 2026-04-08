import os
import requests
from google import genai
import re
import time
from datetime import datetime

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
    "Wizards and Warriors": "UCwqY9GjXBdSYeUZiinbFXyQ"
}

def get_latest_vid(channel_id):
    try:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        r = requests.get(url, timeout=15)
        vids = re.findall(r'<yt:videoId>(.*?)</yt:videoId>', r.text)
        titles = re.findall(r'<title>(.*?)</title>', r.text)
        return (vids[0], titles[1]) if vids else (None, None)
    except:
        return (None, None)

if __name__ == "__main__":
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    rss_items = ""
    
    for name, cid in CHANNELS.items():
        vid, v_title = get_latest_vid(cid)
        if vid:
            url = f"https://www.youtube.com/watch?v={vid}"
            print(f"Processing: {name}...")
            
            summary = ""
            # --- RETRY LOGIC (Attempts up to 3 times) ---
            for attempt in range(3):
                try:
                    prompt = f"Summarize this YouTube video in 3 short bullet points in Italian. Title: {v_title} URL: {url}"
                    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
                    summary = response.text.strip().replace("\n", "<br>")
                    break # Success! Exit the retry loop
                except Exception as e:
                    if "429" in str(e):
                        print(f"Quota hit for {name}. Waiting 30s to retry...")
                        time.sleep(30) # Wait longer if we hit the limit
                    else:
                        print(f"Error for {name}: {e}")
                        summary = "Summary temporarily unavailable."
                        break
            
            rss_items += f"""
            <item>
                <title>{name}: {v_title}</title>
                <link>{url}</link>
                <description>{summary or 'Summary failed after retries.'}</description>
                <pubDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
                <guid isPermaLink="false">{vid}</guid>
            </item>"""
            
            # Pause 10 seconds between every channel to stay under the RPM limit
            time.sleep(10)

    rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0">
    <channel>
        <title>YouTube Intelligence</title>
        <link>https://github.com/lucabenvenuti/ytTranscripts</link>
        <description>AI Summaries</description>
        {rss_items}
    </channel>
    </rss>"""

    with open("feed.xml", "w", encoding="utf-8") as f:
        f.write(rss_feed)
    print("Success: feed.xml updated.")
