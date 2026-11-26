#!/usr/bin/env python3
"""
edit_with_sound.py - Join the provided clips into one 9:16 video, tag a handle on
screen, and lay a background sound underneath WITHOUT overpowering the clips.

How the sound is kept in the background:
  - The sound is turned down (default 18% volume).
  - It "ducks" (gets quieter still) automatically whenever the clips have audio,
    using sidechain compression keyed on the clip audio.
  - It fades in at the start and fades out at the end.
  - The clip audio is kept at full level; the final mix is loudness-normalized.

Example:
  python3 edit_with_sound.py --videos clip1.mp4 clip2.mp4 clip3.mp4 \
      --sound song.mp3 --tag @visionplayent --output final.mp4
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

W, H = 1080, 1920
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def ff_path(p):
    return p.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def probe(path, entries, stream):
    return subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", stream,
         "-show_entries", entries, "-of", "csv=p=0", path],
        capture_output=True, text=True).stdout.strip()


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    return float(out)


def main():
    ap = argparse.ArgumentParser(description="Clips + background sound + tag")
    ap.add_argument("--videos", nargs="+", required=True, help="Clips, in order")
    ap.add_argument("--sound", default=None, help="Background sound/music file (optional)")
    ap.add_argument("--tag", default="@visionplayent", help="Handle shown on screen")
    ap.add_argument("--sound-volume", type=float, default=0.18,
                    help="Background sound level, 0-1 (default 0.18)")
    ap.add_argument("--no-duck", action="store_true",
                    help="Don't lower the sound further while clips have audio")
    ap.add_argument("--tag-y", type=float, default=0.88,
                    help="Vertical position of the tag, 0=top 1=bottom (default 0.88)")
    ap.add_argument("--font", default=None)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            sys.exit(f"{tool} is not installed.")
    for p in a.videos + ([a.sound] if a.sound else []):
        if not os.path.exists(p):
            sys.exit(f"File not found: {p}")

    font = a.font or next((f for f in FONT_CANDIDATES if os.path.exists(f)), None)
    if not font:
        sys.exit("No bold font found. Pass --font /path/to/font.ttf")

    tmp = tempfile.mkdtemp()
    tag_file = os.path.join(tmp, "tag.txt")
    with open(tag_file, "w") as f:
        f.write(a.tag)

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats"]
    parts, concat_in = [], ""
    total = 0.0
    for i, v in enumerate(a.videos):
        cmd += ["-i", v]
        d = duration(v)
        total += d
        # Fit each clip into 9:16 over a blurred copy of itself (no black bars).
        parts.append(
            f"[{i}:v]fps={a.fps},split=2[bg{i}][fg{i}];"
            f"[bg{i}]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"boxblur=30:5,eq=brightness=-0.08[bgb{i}];"
            f"[fg{i}]scale={W}:{H}:force_original_aspect_ratio=decrease[fgs{i}];"
            f"[bgb{i}][fgs{i}]overlay=(W-w)/2:(H-h)/2,setsar=1,format=yuv420p[v{i}]")
        if probe(v, "stream=index", "a"):
            parts.append(f"[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo[a{i}]")
        else:  # silent clip: give it a silent track so concat works
            parts.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{d:.3f}[a{i}]")
        concat_in += f"[v{i}][a{i}]"

    n = len(a.videos)
    snd_idx = n
    if a.sound:
        cmd += ["-stream_loop", "-1", "-i", a.sound]  # loop sound if shorter than video

    parts.append(f"{concat_in}concat=n={n}:v=1:a=1[vcat][clipa]")
    parts.append(
        f"[vcat]drawtext=fontfile='{ff_path(font)}':textfile='{ff_path(tag_file)}':"
        "fontsize=64:fontcolor=white:borderw=4:bordercolor=black@0.8:"
        "box=1:boxcolor=black@0.45:boxborderw=18:"
        f"x=(w-text_w)/2:y=(h-text_h)*{a.tag_y}[v]")

    if not a.sound:
        parts.append("[clipa]loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    else:
        fade_out = max(total - 1.5, 0)
        parts.append(
            f"[{snd_idx}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
            f"atrim=0:{total:.3f},volume={a.sound_volume},"
            f"afade=t=in:d=1,afade=t=out:st={fade_out:.3f}:d=1.5[music]")

        if a.no_duck:
            parts.append("[clipa]volume=1[voice]")
            music = "music"
        else:
            parts.append("[clipa]asplit=2[voice][key]")
            parts.append("[music][key]sidechaincompress=threshold=0.03:ratio=6:"
                         "attack=20:release=400[ducked]")
            music = "ducked"
        parts.append(f"[voice][{music}]amix=inputs=2:duration=first:normalize=0,"
                     "loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    cmd += ["-filter_complex", ";".join(parts), "-map", "[v]", "-map", "[a]",
            "-t", f"{total:.3f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", a.output]
    subprocess.run(cmd, check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\nDone: {a.output} ({total:.1f}s, {W}x{H}, tag {a.tag})")


if __name__ == "__main__":
    main()
