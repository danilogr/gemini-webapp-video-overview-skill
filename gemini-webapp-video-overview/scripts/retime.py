#!/usr/bin/env python3
"""Time the narration to the real audio, and write the captions.

    python3 retime.py DIR

This is what makes the audio the master clock. It measures every
DIR/audio/line_<id>.wav and writes each line's true "start" and "end" back into
narration.json, plus "total_seconds". record.cjs then schedules every action
against those numbers ("L4.start+0.9"), so the pointer lands on the words.
Never hand-edit a start or an end: change the words, re-synthesize, re-run this.

Spacing, from narration.json (seconds): "lead" before the first line (0.5),
"gap" between lines (0.45), "tail" after the last (1.4). A line may carry its
own "pause" — extra seconds before it — to leave room for an action the
narration waits on (a slow page, a dialog opening).

Writes DIR/transcript.vtt and DIR/transcript.srt.
"""
import json
import pathlib
import sys
import wave

if len(sys.argv) < 2:
    sys.exit("usage: retime.py DIR")
V = pathlib.Path(sys.argv[1]).resolve()
nar = json.load(open(V / "narration.json"))
LEAD, GAP, TAIL = nar.get("lead", 0.5), nar.get("gap", 0.45), nar.get("tail", 1.4)


def seconds(p):
    with wave.open(str(p), "rb") as w:
        return w.getnframes() / w.getframerate()


t = LEAD
for i, l in enumerate(nar["lines"]):
    p = V / "audio" / f"line_{l['id']:02d}.wav"
    if not p.exists():
        sys.exit(f"no audio for line {l['id']}: run the TTS step first")
    t += l.get("pause", 0)
    d = seconds(p)
    l["start"], l["end"], l["_dur"] = round(t, 2), round(t + d, 2), round(d, 2)
    t = l["end"] + GAP
nar["total_seconds"] = round(t - GAP + TAIL, 2)
json.dump(nar, open(V / "narration.json", "w"), ensure_ascii=False, indent=2)


def ts(x, sep):
    h, m, s = int(x // 3600), int((x % 3600) // 60), x % 60
    return f"{h:02d}:{m:02d}:{int(s):02d}{sep}{int(round((s - int(s)) * 1000)):03d}"


vtt, srt = ["WEBVTT", ""], []
for i, l in enumerate(nar["lines"], 1):
    vtt += [f"{ts(l['start'], '.')} --> {ts(l['end'], '.')}", l["text"], ""]
    srt += [str(i), f"{ts(l['start'], ',')} --> {ts(l['end'], ',')}", l["text"], ""]
(V / "transcript.vtt").write_text("\n".join(vtt))
(V / "transcript.srt").write_text("\n".join(srt))

print("retimed. total =", nar["total_seconds"], "s")
for l in nar["lines"]:
    print(f"  L{l['id']:>2} {l['start']:6.2f}–{l['end']:6.2f} ({l['_dur']:.2f}s)  {l['text'][:50]}")
