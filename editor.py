"""Agente editor: descarga (solo licenciados), elige el mejor tramo y lo pasa a 9:16."""
import subprocess, tempfile, numpy as np
from common import sb
CLIP_S = 30

def best_window(path):
    raw = subprocess.run(["ffmpeg","-v","quiet","-i",path,"-ac","1","-ar","8000","-f","s16le","-"],
                         capture_output=True).stdout
    a = np.frombuffer(raw, dtype=np.int16).astype(float)
    per_s = [np.sqrt(np.mean(a[i:i+8000]**2)) for i in range(0, len(a)-8000, 8000)]
    if len(per_s) <= CLIP_S: return 0
    sums = np.convolve(per_s, np.ones(CLIP_S), "valid")
    return int(np.argmax(sums))

def run():
    q = sb.table("videos").select("*").eq("status","found").in_("license",["creativeCommon","authorized"]).limit(3).execute()
    for v in q.data:
        sb.table("videos").update({"status":"editing"}).eq("id", v["id"]).execute()
        d = tempfile.mkdtemp(); src = f"{d}/src.mp4"; out = f"{d}/clip.mp4"
        try:
            subprocess.run(["yt-dlp","-f","mp4[height<=720]","-o",src,v["source_url"]], check=True)
            s = best_window(src)
            subprocess.run(["ffmpeg","-y","-ss",str(s),"-t",str(CLIP_S),"-i",src,
              "-vf","scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
              "-c:v","libx264","-preset","veryfast","-c:a","aac",out], check=True)
            sb.table("videos").update({"status":"edited","clip_path":out,
                "error":None,"raw_path":str(s)}).eq("id", v["id"]).execute()
        except Exception as e:
            sb.table("videos").update({"status":"failed","error":str(e)[:300]}).eq("id", v["id"]).execute()

if __name__ == "__main__": run()
