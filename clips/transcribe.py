#!/usr/bin/env python3
"""Word-timestamp transcript for captions:  HF_HUB_DISABLE_XET=1 python3 -I clips/transcribe.py VIDEO OUT.json"""
import sys, json
from faster_whisper import WhisperModel
m = WhisperModel("medium.en", device="cpu", compute_type="int8")
import subprocess, numpy as np
pcm = subprocess.run(["ffmpeg","-v","error","-i",sys.argv[1],"-ac","1","-ar","16000","-f","s16le","-"],capture_output=True,check=True).stdout
audio = np.frombuffer(pcm, np.int16).astype(np.float32)/32768
segs, _ = m.transcribe(audio, word_timestamps=True, vad_filter=False)
out = []
for s in segs:
    print(f"{s.start:6.2f}-{s.end:6.2f} {s.text}")
    out.append({"start": s.start, "end": s.end, "text": s.text.strip(),
                "words": [[w.start, w.end, w.word] for w in s.words]})
json.dump(out, open(sys.argv[2], "w"), indent=1)
