"""Agente buscador: videos virales con licencia Creative Commons (o de fuentes autorizadas)."""
import os, datetime, requests
from common import sb
KEY = os.environ["YOUTUBE_API_KEY"]
QUERIES = os.environ.get("QUERIES", "funny,sports,science").split(",")

def run():
    since = (datetime.datetime.utcnow() - datetime.timedelta(days=7)).isoformat("T") + "Z"
    for q in QUERIES:
        r = requests.get("https://www.googleapis.com/youtube/v3/search", params={
            "part": "snippet", "type": "video", "q": q, "order": "viewCount",
            "videoLicense": "creativeCommon", "publishedAfter": since,
            "maxResults": 10, "key": KEY}).json()
        ids = [i["id"]["videoId"] for i in r.get("items", [])]
        if not ids: continue
        stats = requests.get("https://www.googleapis.com/youtube/v3/videos", params={
            "part": "statistics,snippet", "id": ",".join(ids), "key": KEY}).json()
        for v in stats.get("items", []):
            sb.table("videos").upsert({
                "platform": "youtube", "source_url": f"https://youtu.be/{v['id']}",
                "title": v["snippet"]["title"], "author": v["snippet"]["channelTitle"],
                "license": "creativeCommon", "views": int(v["statistics"].get("viewCount", 0)),
            }, on_conflict="source_url", ignore_duplicates=True).execute()

if __name__ == "__main__": run()
