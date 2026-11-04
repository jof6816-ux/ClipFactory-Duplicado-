import os, re, time, uuid, tempfile, subprocess
from pathlib import Path
from supabase import create_client

SUPABASE_URL = os.environ['SUPABASE_URL']
SERVICE_KEY = os.environ['SUPABASE_SERVICE_KEY']
POLL_SECONDS = int(os.getenv('POLL_SECONDS', '8'))
MAX_CLIPS = int(os.getenv('MAX_CLIPS_PER_VIDEO', '3'))
CLIP_SECONDS = int(os.getenv('CLIP_SECONDS', '25'))
BUCKET_IN = os.getenv('INPUT_BUCKET', 'uploads')
BUCKET_OUT = os.getenv('OUTPUT_BUCKET', 'clips')
sb = create_client(SUPABASE_URL, SERVICE_KEY)


def run_cmd(args):
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if p.returncode:
        raise RuntimeError((p.stderr or 'FFmpeg failed')[-1800:])
    return p


def duration(path):
    p = run_cmd(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',path])
    return max(0.0, float(p.stdout.strip()))


def scene_times(path):
    # Detect meaningful visual transitions; the first frame is always a candidate.
    p = subprocess.run(['ffmpeg','-hide_banner','-i',path,'-vf',"select='gt(scene,0.28)',showinfo",'-an','-f','null','-'],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    times = [0.0]
    for line in p.stderr.splitlines():
        m = re.search(r'pts_time:([0-9.]+)', line)
        if m:
            t = float(m.group(1))
            if t > 1:
                times.append(t)
    return sorted(set(times))


def choose_segments(path, total):
    if total <= 0:
        raise RuntimeError('No se pudo leer la duración del vídeo')
    length = min(CLIP_SECONDS, max(5, total))
    candidates = scene_times(path)
    # Keep candidates with enough material after the transition.
    candidates = [t for t in candidates if t + length <= total + 0.25]
    if not candidates:
        candidates = [max(0.0, (total - length) / 2)]
    # Spread the selected scenes across the source instead of taking adjacent cuts.
    chosen = []
    for t in candidates:
        if all(abs(t - old) >= length * 0.8 for old in chosen):
            chosen.append(t)
        if len(chosen) >= MAX_CLIPS:
            break
    return [(t, min(length, total - t)) for t in chosen]


def process_job(job):
    job_id = str(job['id'])
    src_key = job.get('input_path') or job.get('storage_path')
    if not src_key:
        raise RuntimeError('El trabajo no contiene input_path/storage_path')
    src_key = src_key.lstrip('/')
    with tempfile.TemporaryDirectory(prefix='clipfactory-') as td:
        src = str(Path(td) / 'source_video')
        # Supabase Storage download returns the original bytes.
        data = sb.storage.from_(BUCKET_IN).download(src_key)
        Path(src).write_bytes(data)
        total = duration(src)
        segments = choose_segments(src, total)
        parts = []
        for idx, (start, length) in enumerate(segments, 1):
            part = str(Path(td) / f'part-{idx}.mp4')
            run_cmd(['ffmpeg','-y','-ss',f'{start:.3f}','-i',src,'-t',f'{length:.3f}',
                     '-vf',"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30",
                     '-c:v','libx264','-preset','veryfast','-crf','23','-c:a','aac','-b:a','128k',
                     '-movflags','+faststart',part])
            parts.append(part)
        concat = str(Path(td) / 'concat.txt')
        Path(concat).write_text(''.join(f"file '{p}'\n" for p in parts))
        final = str(Path(td) / 'highlight.mp4')
        run_cmd(['ffmpeg','-y','-f','concat','-safe','0','-i',concat,'-c','copy','-movflags','+faststart',final])
        out_key = f'{job_id}/{uuid.uuid4().hex}-highlight.mp4'
        sb.storage.from_(BUCKET_OUT).upload(out_key, Path(final).read_bytes(),
            file_options={'content-type':'video/mp4','upsert':'true'})
        sb.table('processing_jobs').update({
            'status':'done', 'output_path':out_key, 'error':None
        }).eq('id', job_id).execute()


def claim_next():
    rows = sb.table('processing_jobs').select('*').eq('status','queued').order('created_at').limit(1).execute().data
    if not rows:
        return None
    job = rows[0]
    changed = sb.table('processing_jobs').update({'status':'processing','error':None}).eq('id',job['id']).eq('status','queued').execute().data
    return job if changed else None


def main():
    print('ClipFactory FFmpeg worker online; polling Supabase queue', flush=True)
    while True:
        try:
            job = claim_next()
            if not job:
                time.sleep(POLL_SECONDS)
                continue
            try:
                print(f"Processing job {job['id']}", flush=True)
                process_job(job)
                print(f"Completed job {job['id']}", flush=True)
            except Exception as exc:
                msg = str(exc)[:1500]
                sb.table('processing_jobs').update({'status':'failed','error':msg}).eq('id',job['id']).execute()
                print(f"Job {job['id']} failed: {msg}", flush=True)
        except Exception as exc:
            print(f'Queue error: {exc}', flush=True)
            time.sleep(POLL_SECONDS)

if __name__ == '__main__':
    main()
