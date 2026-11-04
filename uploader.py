"""Agente multiplataforma: publica los clips en YouTube Shorts, TikTok e Instagram Reels.
Activa plataformas con PUBLISH_TO=youtube,tiktok,instagram. Cada una requiere su app aprobada."""
import os, time, requests
from common import sb
TARGETS = [t for t in os.environ.get("PUBLISH_TO", "").split(",") if t]

def caption(clip):  # incluye el crédito del autor original
    return (clip["credit"] or "")[:2000]

# ---------- YouTube Shorts (YouTube Data API, OAuth) ----------
def yt_token():
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"})
    r.raise_for_status(); return r.json()["access_token"]

def post_youtube(clip, data):
    h = {"Authorization": f"Bearer {yt_token()}", "Content-Type": "application/json",
         "X-Upload-Content-Type": "video/mp4"}
    meta = {"snippet": {"title": (clip.get("title") or "Clip")[:90] + " #Shorts", "description": caption(clip) + "\n#Shorts"},
            "status": {"privacyStatus": os.environ.get("YT_PRIVACY", "private"),
                       "selfDeclaredMadeForKids": False}}
    init = requests.post("https://www.googleapis.com/upload/youtube/v3/videos"
                         "?uploadType=resumable&part=snippet,status", headers=h, json=meta)
    init.raise_for_status()
    up = requests.put(init.headers["Location"], data=data, headers={"Content-Type": "video/mp4"})
    up.raise_for_status(); return up.json()["id"]

# ---------- TikTok (Content Posting API; sin auditoría solo publica privado) ----------
def post_tiktok(clip, data):
    h = {"Authorization": f"Bearer {os.environ['TIKTOK_ACCESS_TOKEN']}",
         "Content-Type": "application/json; charset=UTF-8"}
    size = len(data)
    init = requests.post("https://open.tiktokapis.com/v2/post/publish/video/init/", headers=h, json={
        "post_info": {"title": caption(clip)[:150],
                      "privacy_level": os.environ.get("TIKTOK_PRIVACY", "SELF_ONLY")},
        "source_info": {"source": "FILE_UPLOAD", "video_size": size,
                        "chunk_size": size, "total_chunk_count": 1}}).json()
    d = init["data"]
    requests.put(d["upload_url"], data=data, headers={"Content-Type": "video/mp4",
        "Content-Range": f"bytes 0-{size-1}/{size}"}).raise_for_status()
    return d["publish_id"]

# ---------- Instagram Reels (Graph API; necesita URL pública del video) ----------
def post_instagram(clip, data):
    ig, tok = os.environ["IG_USER_ID"], os.environ["IG_ACCESS_TOKEN"]
    url = sb.storage.from_("clips").create_signed_url(clip["storage_path"], 3600)["signedURL"]
    if not url.startswith("http"): url = os.environ["SUPABASE_URL"] + "/storage/v1" + url
    c = requests.post(f"https://graph.facebook.com/v21.0/{ig}/media", data={
        "media_type": "REELS", "video_url": url, "caption": caption(clip), "access_token": tok}).json()
    cid = c["id"]
    for _ in range(30):  # espera a que Instagram procese el video
        st = requests.get(f"https://graph.facebook.com/v21.0/{cid}",
            params={"fields": "status_code", "access_token": tok}).json().get("status_code")
        if st == "FINISHED": break
        if st == "ERROR": raise RuntimeError("Instagram rechazó el video")
        time.sleep(10)
    p = requests.post(f"https://graph.facebook.com/v21.0/{ig}/media_publish",
        data={"creation_id": cid, "access_token": tok}).json()
    return p["id"]

POSTERS = {"youtube": post_youtube, "tiktok": post_tiktok, "instagram": post_instagram}

def run():
    if not TARGETS: return
    clips = sb.table("clips").select("*, videos(title)").execute().data
    for clip in clips:
        clip["title"] = (clip.get("videos") or {}).get("title")
        data = None
        for plat in TARGETS:
            done = sb.table("publications").select("id").eq("clip_id", clip["id"]).eq("platform", plat).execute().data
            if done: continue
            try:
                data = data or sb.storage.from_("clips").download(clip["storage_path"])
                ext = POSTERS[plat](clip, data)
                sb.table("publications").insert({"clip_id": clip["id"], "platform": plat,
                    "status": "done", "external_id": str(ext)}).execute()
            except Exception as e:
                sb.table("publications").insert({"clip_id": clip["id"], "platform": plat,
                    "status": "failed", "error": str(e)[:300]}).execute()

if __name__ == "__main__": run()
