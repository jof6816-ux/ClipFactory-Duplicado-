"""Agente publicador: sube el clip al almacenamiento y lo hace visible en la web."""
import os
from common import sb

def run():
    for v in sb.table("videos").select("*").eq("status","edited").execute().data:
        if not v["clip_path"] or not os.path.exists(v["clip_path"]):
            sb.table("videos").update({"status": "found"}).eq("id", v["id"]).execute()
            continue
        path = f"{v['id']}.mp4"
        with open(v["clip_path"], "rb") as f:
            sb.storage.from_("clips").upload(path, f, {"content-type":"video/mp4","upsert":"true"})
        start = int(v["raw_path"] or 0)
        sb.table("clips").insert({"video_id":v["id"],"storage_path":path,
            "credit": f"{v['title']} — {v['author']} (CC BY) {v['source_url']}",
            "start_s":start,"end_s":start+30}).execute()
        sb.table("videos").update({"status":"published"}).eq("id", v["id"]).execute()

if __name__ == "__main__": run()
