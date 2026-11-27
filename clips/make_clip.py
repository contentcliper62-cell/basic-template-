#!/usr/bin/env python3
"""Render a 9:16 tune-in clip for "Checking Inn for Christmas".

  python3 clips/make_clip.py clips/specs/clip1.json [--post-at 2026-11-28T12:00]

Spec (JSON):
  source       path to the scene file from Frame.io (original footage, untouched)
  segments     [[in, out], ...] to join several shots into one clip (overrides in/out)
  in, out      timestamps in the source ("00:12:03.5" or seconds). Cut ON the cliffhanger.
  hook         on-screen hook text, shown for the first `hook_secs` (default 3.0)
  captions     path to a word-timestamp transcript (.json, from transcribe.py) OR an .srt for the cut (times relative to the source or to `in`, see
               captions_relative) OR a list of [start, end, "text"] relative to `in`
  captions_relative  "in" (default) or "source"
  fit          "crop" (fill frame, use crop_x 0..1 to pick the focus) or "blur" (whole
               frame over a blurred copy; best for two-shots)
  crop_x       0..1 horizontal focus for crop mode (0.5 = centre)
  end_card     end card image; "{phase}" is replaced by sat/tonight/streaming
               (default clips/refs/cards/endcard_{phase}.png, built by make_cards.py)
  end_secs     end card length (2-3 s, default 2.5)
  output       output .mp4 path

The CTA line is chosen from the planned POST time (US Eastern), not the render time:
  before Sat Nov 28      -> "premieres Sat., Nov. 28 at 10/9c on Lifetime"
  Nov 28 before 10pm ET  -> "TONIGHT at 10/9c on Lifetime"
  after the premiere     -> "Streaming now on Lifetime"
"""
import argparse, json, re, subprocess, sys, tempfile, os
from datetime import datetime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
PREMIERE = datetime(2026, 11, 28, 22, 0, tzinfo=ET)
TITLE = "Checking Inn for Christmas"
W, H = 1080, 1920
FONT = "Inter"


def phase_for(post_at: datetime) -> str:
    if post_at.date() < PREMIERE.date():
        return "sat"
    return "tonight" if post_at < PREMIERE else "streaming"


CTAS = {
    "sat": f"{TITLE} premieres Sat., Nov. 28 at 10/9c on Lifetime",
    "tonight": f"{TITLE} premieres TONIGHT at 10/9c on Lifetime",
    "streaming": f"{TITLE} is streaming now on Lifetime",
}


def secs(t) -> float:
    if isinstance(t, (int, float)):
        return float(t)
    parts = [float(p) for p in str(t).replace(",", ".").split(":")]
    v = 0.0
    for p in parts:
        v = v * 60 + p
    return v


def ass_time(t: float) -> str:
    t = max(t, 0)
    h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def ass_text(s: str) -> str:
    return s.replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", "\\N")


def word_captions(path, segments, max_chars=30, max_gap=0.6):
    """Short caption chunks from a word-timestamp transcript, remapped onto the cut."""
    words = [w for seg in json.load(open(path)) for w in seg["words"]]
    out, offset = [], 0.0
    for a, b in segments:
        chunk = []
        def flush():
            if chunk:
                out.append((chunk[0][0], chunk[-1][1] + 0.15, " ".join(t for _, _, t in chunk).replace(" -", "-")))
                chunk.clear()
        for ws, we, t in words:
            mid = (ws + we) / 2
            if not a <= mid < b:
                continue
            ws, we, t = ws - a + offset, min(we, b) - a + offset, t.strip()
            if chunk and (len(" ".join(x[2] for x in chunk)) + len(t) > max_chars
                          or ws - chunk[-1][1] > max_gap or chunk[-1][2][-1] in ".?!"):
                flush()
            chunk.append((ws, we, t))
        flush()
        offset += b - a
    # no overlaps; never run past the next chunk
    return [(a, min(b, out[i + 1][0]) if i + 1 < len(out) else b, t) for i, (a, b, t) in enumerate(out)]


def load_captions(spec, start, dur):
    cap = spec.get("captions") or []
    if isinstance(cap, str) and cap.endswith(".json"):
        return [c for c in word_captions(cap, spec["_segments"]) if c[0] < dur]
    rel = spec.get("captions_relative", "in")
    items = []
    if isinstance(cap, str):
        raw = open(cap, encoding="utf-8-sig").read()
        for block in re.split(r"\n\s*\n", raw.strip()):
            lines = block.strip().splitlines()
            ts = next((l for l in lines if "-->" in l), None)
            if not ts:
                continue
            a, b = [secs(x.strip().split()[0]) for x in ts.split("-->")]
            text = "\n".join(lines[lines.index(ts) + 1:])
            text = re.sub(r"<[^>]+>", "", text)
            items.append((a, b, text))
    else:
        items = [(secs(a), secs(b), t) for a, b, t in cap]
    if isinstance(cap, str) and rel == "source":
        items = [(a - start, b - start, t) for a, b, t in items]
    return [(max(a, 0), min(b, dur), t) for a, b, t in items if b > 0 and a < dur]


def build_ass(path, hook, hook_secs, caps, cta, dur, end_secs):
    total = dur + end_secs
    hdr = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hook,{FONT},76,&H00FFFFFF,&H00FFFFFF,&H00203AB0,&H00203AB0,1,0,0,0,100,100,0,0,3,22,0,8,70,70,230,1
Style: Cap,{FONT},74,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,5,2,2,80,80,560,1
Style: CTA,{FONT},50,&H00FFFFFF,&H00FFFFFF,&H00203AB0,&H00203AB0,1,0,0,0,100,100,0,0,3,18,0,2,70,70,330,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    ev.append(f"Dialogue: 2,{ass_time(0)},{ass_time(min(hook_secs, dur))},Hook,,0,0,0,,{{\\fad(0,250)}}{ass_text(hook)}")
    for a, b, t in caps:
        ev.append(f"Dialogue: 1,{ass_time(a)},{ass_time(b)},Cap,,0,0,0,,{ass_text(t)}")
    # CTA banner over the last 4 s of the scene; the end card carries its own date block
    ev.append(f"Dialogue: 3,{ass_time(max(dur - 4, hook_secs))},{ass_time(dur)},CTA,,0,0,0,,{ass_text(cta)}")
    open(path, "w", encoding="utf-8").write(hdr + "\n".join(ev) + "\n")


def ffprobe_aspect(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout.strip().split(",")
    return int(out[0]) / int(out[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--post-at", help="planned post time, ET, e.g. 2026-11-28T12:00 (default: now)")
    args = ap.parse_args()
    spec = json.load(open(args.spec))
    post_at = datetime.fromisoformat(args.post_at).replace(tzinfo=ET) if args.post_at else datetime.now(ET)
    phase = phase_for(post_at)
    cta = spec.get("cta") or CTAS[phase]
    end_card = spec.get("end_card", "clips/refs/cards/endcard_{phase}.png").format(phase=phase)

    segments = [(secs(a), secs(b)) for a, b in spec["segments"]] if "segments" in spec \
        else [(secs(spec["in"]), secs(spec["out"]))]
    spec["_segments"] = segments
    start = segments[0][0]
    dur = sum(b - a for a, b in segments)
    end_secs = float(spec.get("end_secs", 2.5))
    if not 2 <= end_secs <= 3:
        sys.exit("end_secs must be 2-3 s")
    if not 15 <= dur + end_secs <= 60:
        sys.exit(f"clip would be {dur + end_secs:.1f}s; must be 15-60 s total")

    out = spec["output"].format(phase=phase)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    tmp = tempfile.mkdtemp()
    ass = os.path.join(tmp, "overlay.ass")
    build_ass(ass, spec["hook"], float(spec.get("hook_secs", 3.0)),
              load_captions(spec, start, dur), cta, dur, end_secs)

    # cut + join the source segments (tiny audio fades hide the joins)
    parts = []
    for i, (a, b) in enumerate(segments):
        d = b - a
        parts.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];"
                     f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.06,afade=t=out:st={d - 0.08}:d=0.08[a{i}]")
    joins = "".join(f"[v{i}][a{i}]" for i in range(len(segments)))
    cut = ";".join(parts) + f";{joins}concat=n={len(segments)}:v=1:a=1[src][srca]"

    fit = spec.get("fit", "blur")
    if fit == "crop":
        cx = float(spec.get("crop_x", 0.5))
        scene = f"[src]scale=-2:{H},crop={W}:{H}:'(iw-{W})*{cx}':0,setsar=1,fps=30[sv]"
    else:
        scene = (f"[src]split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                 f"boxblur=30:3,eq=brightness=-0.12[bg];[b]scale={W}:-2[fg];"
                 f"[bg][fg]overlay=0:(H-h)/2,setsar=1,fps=30[sv]")
    card_is_vertical = abs(ffprobe_aspect(end_card) - W / H) < 0.02
    card = (f"[1:v]scale={W}:{H},setsar=1,fps=30,trim=duration={end_secs}[cv]" if card_is_vertical else f"[1:v]split[c1][c2];[c1]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"boxblur=40:3,eq=brightness=-0.2[cbg];[c2]scale={W - 120}:{H - 700}:force_original_aspect_ratio=decrease[cfg];"
            f"[cbg][cfg]overlay=(W-w)/2:(H-h)/2-120,setsar=1,fps=30,trim=duration={end_secs}[cv]")
    ass_esc = ass.replace(":", r"\:")
    fc = (f"{cut};{scene};{card};"
          f"[srca]aresample=48000,afade=t=out:st={dur - 0.6}:d=0.6[sa];"
          f"[2:a]atrim=duration={end_secs}[ca];"
          f"[sv][sa][cv][ca]concat=n=2:v=1:a=1[v][a];"
          f"[v]subtitles='{ass_esc}':fontsdir=/usr/share/fonts[vo]")
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-i", spec["source"],
           "-loop", "1", "-t", str(end_secs), "-i", end_card,
           "-f", "lavfi", "-t", str(end_secs), "-i", "anullsrc=r=48000:cl=stereo",
           "-filter_complex", fc, "-map", "[vo]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print(f"wrote {out}  ({dur + end_secs:.1f}s)  CTA: {cta}")


if __name__ == "__main__":
    main()
