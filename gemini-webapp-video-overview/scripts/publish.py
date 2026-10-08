#!/usr/bin/env python3
"""Put a built video's captions and poster beside it, and list the videos.

    python3 publish.py SLUG DIR PUB              # PUB/SLUG.vtt and PUB/SLUG.jpg
    python3 publish.py --list ROOT PUB SLUG…     # PUB/videos.json, in that order

The captions are retime.py's transcript.vtt. build.sh cuts the recording at
the instant the clock started, so the audio — and so the captions — start
exactly where narration.json says. The poster is the frame at narration.json's
"poster" (a time, written like an action's "at": "L2.end+0.5"), else the
middle of the video. Pick a frame that shows the feature, not the empty start.
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys


def duration(mp4):
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nokey=1:noprint_wrappers=1", str(mp4)],
        capture_output=True, text=True, check=True).stdout.strip())


def resolve(at, nar):
    m = re.fullmatch(r"L(\d+)\.(start|end)([+-][\d.]+)?", str(at))
    if not m:
        return float(at)
    line = next(l for l in nar["lines"] if l["id"] == int(m[1]))
    return line[m[2]] + float(m[3] or 0)


if len(sys.argv) > 1 and sys.argv[1] == "--list":
    root, pub = pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
    out = []
    for slug in sys.argv[4:]:
        mp4 = pub / f"{slug}.mp4"
        if not mp4.exists():
            continue
        nar = json.load(open(root / slug / "narration.json"))
        out.append({"slug": slug, "title": nar.get("title", slug), "seconds": round(duration(mp4))})
    (pub / "videos.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    for v in out:
        print(f"  {v['seconds']:>3} s  {v['slug']:<16} {v['title']}")
    raise SystemExit(0)

if len(sys.argv) != 4:
    sys.exit(__doc__)
slug, d, pub = sys.argv[1], pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
nar = json.load(open(d / "narration.json"))
mp4 = pub / f"{slug}.mp4"
shutil.copyfile(d / "transcript.vtt", pub / f"{slug}.vtt")
t = resolve(nar["poster"], nar) if "poster" in nar else duration(mp4) / 2
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", str(mp4),
                "-frames:v", "1", "-q:v", "5", str(pub / f"{slug}.jpg")], check=True)
print(f"published {slug}: poster at {t:.2f} s")
