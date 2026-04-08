import os
import requests
import google.generativeai as genai
import re
from datetime import datetime

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
    except: return (None, None)

if __name__ == "__main__":
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    rss_items = ""
    for name, cid in CHANNELS.items():
        vid, v_title = get_latest_vid(cid)
        if vid:
            url = f"https://www.youtube.com/watch?v={vid}"
            try:
                res = model.generate_content(f"Summarize in 3 bullets: {url}")
                summary = res.text.replace("\n", "<br>")
            except: summary = "Summary failed."
            
            rss_items += f"""
            <item>
                <title>{name}: {v_title}</title>
                <link>{url}</link>
                <description>{summary}</description>
                <pubDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
            </item>"""

    rss_feed = f"""<?xml version="1.0" encoding="UTF-8" ?>
    <rss version="2.0">
    <channel>
        <title>My YouTube Intelligence</title>
        <link>https://github.com/{os.getenv('GITHUB_REPOSITORY')}</link>
        <description>Latest AI Summaries</description>
        {rss_items}
    </channel>
    </rss>"""

    with open("feed.xml", "w") as f:
        f.write(rss_feed)
