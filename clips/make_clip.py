#!/usr/bin/env python3
"""Render a 9:16 tune-in clip for "Checking Inn for Christmas".

  python3 clips/make_clip.py clips/specs/clip1.json [--post-at 2026-11-28T12:00]

Spec (JSON):
  source       path to the scene file from Frame.io (original footage, untouched)
  in, out      timestamps in the source ("00:12:03.5" or seconds). Cut ON the cliffhanger.
  hook         on-screen hook text, shown for the first `hook_secs` (default 3.0)
  captions     path to an .srt for the cut (times relative to the source or to `in`, see
               captions_relative) OR a list of [start, end, "text"] relative to `in`
  captions_relative  "in" (default) or "source"
  fit          "crop" (fill frame, use crop_x 0..1 to pick the focus) or "blur" (whole
               frame over a blurred copy; best for two-shots)
  crop_x       0..1 horizontal focus for crop mode (0.5 = centre)
  end_card     key art / title logo image for the 2.5 s end card
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


def cta_for(post_at: datetime) -> str:
    if post_at.date() < PREMIERE.date():
        return f"{TITLE} premieres Sat., Nov. 28 at 10/9c on Lifetime"
    if post_at < PREMIERE:
        return f"{TITLE} premieres TONIGHT at 10/9c on Lifetime"
    return f"{TITLE} is streaming now on Lifetime"


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


def load_captions(spec, start, dur):
    cap = spec.get("captions") or []
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
Style: Cap,{FONT},62,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,5,2,2,80,80,560,1
Style: CTA,{FONT},50,&H00FFFFFF,&H00FFFFFF,&H00203AB0,&H00203AB0,1,0,0,0,100,100,0,0,3,18,0,2,70,70,330,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    ev.append(f"Dialogue: 2,{ass_time(0)},{ass_time(min(hook_secs, dur))},Hook,,0,0,0,,{{\\fad(0,250)}}{ass_text(hook)}")
    for a, b, t in caps:
        ev.append(f"Dialogue: 1,{ass_time(a)},{ass_time(b)},Cap,,0,0,0,,{ass_text(t)}")
    # CTA banner: last 4 s of the scene and through the end card
    ev.append(f"Dialogue: 3,{ass_time(max(dur - 4, hook_secs))},{ass_time(total)},CTA,,0,0,0,,{ass_text(cta)}")
    open(path, "w", encoding="utf-8").write(hdr + "\n".join(ev) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--post-at", help="planned post time, ET, e.g. 2026-11-28T12:00 (default: now)")
    args = ap.parse_args()
    spec = json.load(open(args.spec))
    post_at = datetime.fromisoformat(args.post_at).replace(tzinfo=ET) if args.post_at else datetime.now(ET)
    cta = spec.get("cta") or cta_for(post_at)

    start, end = secs(spec["in"]), secs(spec["out"])
    dur = end - start
    end_secs = float(spec.get("end_secs", 2.5))
    if not 2 <= end_secs <= 3:
        sys.exit("end_secs must be 2-3 s")
    if not 15 <= dur + end_secs <= 60:
        sys.exit(f"clip would be {dur + end_secs:.1f}s; must be 15-60 s total")

    out = spec["output"]
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    tmp = tempfile.mkdtemp()
    ass = os.path.join(tmp, "overlay.ass")
    build_ass(ass, spec["hook"], float(spec.get("hook_secs", 3.0)),
              load_captions(spec, start, dur), cta, dur, end_secs)

    fit = spec.get("fit", "blur")
    if fit == "crop":
        cx = float(spec.get("crop_x", 0.5))
        scene = f"[0:v]scale=-2:{H},crop={W}:{H}:'(iw-{W})*{cx}':0,setsar=1,fps=30[sv]"
    else:
        scene = (f"[0:v]split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                 f"boxblur=30:3,eq=brightness=-0.12[bg];[b]scale={W}:-2[fg];"
                 f"[bg][fg]overlay=0:(H-h)/2,setsar=1,fps=30[sv]")
    card = (f"[1:v]split[c1][c2];[c1]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"boxblur=40:3,eq=brightness=-0.2[cbg];[c2]scale={W - 120}:{H - 700}:force_original_aspect_ratio=decrease[cfg];"
            f"[cbg][cfg]overlay=(W-w)/2:(H-h)/2-120,setsar=1,fps=30,trim=duration={end_secs}[cv]")
    ass_esc = ass.replace(":", r"\:")
    fc = (f"{scene};{card};"
          f"[0:a]aresample=48000,afade=t=out:st={dur - 0.6}:d=0.6[sa];"
          f"[2:a]atrim=duration={end_secs}[ca];"
          f"[sv][sa][cv][ca]concat=n=2:v=1:a=1[v][a];"
          f"[v]subtitles='{ass_esc}':fontsdir=/usr/share/fonts[vo]")
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-ss", str(start), "-t", str(dur), "-i", spec["source"],
           "-loop", "1", "-t", str(end_secs), "-i", spec["end_card"],
           "-f", "lavfi", "-t", str(end_secs), "-i", "anullsrc=r=48000:cl=stereo",
           "-filter_complex", fc, "-map", "[vo]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    print(f"wrote {out}  ({dur + end_secs:.1f}s)  CTA: {cta}")


if __name__ == "__main__":
    main()
