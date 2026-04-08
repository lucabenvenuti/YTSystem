import os
import requests
from google import genai
import re
import time
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
        # titles[0] è il titolo del canale, titles[1] è il titolo del video
        return (vids[0], titles[1]) if vids else (None, None)
    except Exception as e:
        print(f"Error fetching feed for {channel_id}: {e}")
        return (None, None)

def get_transcript(video_id):
    try:
        # Metodo standard universale
        srt = YouTubeTranscriptApi.get_transcript(video_id, languages=['it', 'en'])
        full_text = " ".join([i['text'] for i in srt])
        print(f"DEBUG: Transcript found for {video_id}")
        return full_text[:15000]
    except Exception as e:
        print(f"DEBUG: Transcript NOT AVAILABLE for {video_id}. Error: {str(e)[:50]}")
        return None

if __name__ == "__main__":
    # Inizializza client Gemini
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found.")
        exit(1)
        
    client = genai.Client(api_key=api_key)
    rss_items = ""
    # Modello ottimizzato per velocità e costi
    MODEL_NAME = "gemini-2.0-flash-lite-preview-02-05"
    
    for name, cid in CHANNELS.items():
        vid, v_title = get_latest_vid(cid)
        if vid:
            url = f"https://www.youtube.com/watch?v={vid}"
            print(f"Processing {name}...")
            
            # Tenta il recupero del transcript
            transcript_text = get_transcript(vid)
            label = "TRANSCRIPT" if transcript_text else "TITLE-ONLY"
            
            try:
                if transcript_text:
                    source_material = f"TRANSCRIPT CONTENT: {transcript_text}"
                else:
                    source_material = f"VIDEO TITLE: {v_title} (No transcript available)"

                prompt = (
                    f"Analyze the following content from the YouTube video: '{v_title}'.\n"
                    f"Source Data: {source_material}\n\n"
                    "Task:\n"
                    f"1. Start your response with the word '**{label}**' on the first line.\n"
                    "2. Language: If the video content/title is in Italian, write the summary in Italian. "
                    "If it is in English, write in English. Otherwise, use English.\n"
                    "3. Structure: Provide a detailed summary in 5 key points.\n"
                    "4. Depth: Each point must be 2-3 sentences long, explaining the 'what' and the 'why'.\n"
                    "5. Tone: Professional and informative."
                )
                
                response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
                summary = response.text.strip().replace("\n", "<br>")
                
            except Exception as e:
                print(f"Gemini Error for {name}: {e}")
                summary = f"**{label}**<br>Summary failed due to AI provider limits or error."
            
            # Costruzione item RSS con GUID dinamico per forzare refresh in NetNewsWire
            rss_items += f"""
            <item>
                <title>{name}: {v_title}</title>
                <link>{url}</link>
                <description><![CDATA[{summary}]]></description>
                <pubDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
                <guid isPermaLink="false">{vid}-{int(time.time())}</guid>
            </item>"""
            
            # Piccolo delay per non saturare le API
            time.sleep(2)

    # Creazione file XML finale
    rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0">
    <channel>
        <title>YouTube Intelligence</title>
        <link>https://github.com/lucabenvenuti/ytTranscripts</link>
        <description>AI Summaries (Transcripts + Titles)</description>
        {rss_items}
    </channel>
    </rss>"""

    with open("feed.xml", "w", encoding="utf-8") as f:
        f.write(rss_feed)
    
    print("Success: feed.xml updated.")
