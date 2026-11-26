#!/usr/bin/env python3
"""
make_clip.py - Buat klip vertikal 9:16 sesuai aturan kampanye SkiiMaskTimmy.

Hasil:
  - 1080x1920, 30/60 fps, H.264 + AAC (siap TikTok / Reels / Shorts)
  - Facecam besar di atas, gameplay di bawah
  - Teks hook (opsional) di tengah
  - Teks "twitch.tv/skiimasktimmy" selalu tampil di bawah
  - Overlay Twitch PNG (dari Google Drive kampanye) ditaruh di atas semuanya
  - Audio asli stream dipertahankan (hanya dinormalisasi, tanpa musik)

Contoh:
  python3 make_clip.py --input vod.mp4 --start 01:23:45 --end 01:24:12 \
      --facecam 1500,40,400,300 --hook "HE HAD 1 HP..." \
      --overlay overlay.png --output klip1.mp4
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap

W, H = 1080, 1920
CAM_H = 720           # tinggi area facecam
GAME_H = H - CAM_H    # tinggi area gameplay (1200)
HANDLE = "twitch.tv/skiimasktimmy"
MIN_SECONDS = 7

FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/inter/Inter-Black.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def to_seconds(t: str) -> float:
    parts = [float(p) for p in t.split(":")]
    sec = 0.0
    for p in parts:
        sec = sec * 60 + p
    return sec


def find_font(user_font):
    if user_font:
        return user_font
    for f in FONT_CANDIDATES:
        if os.path.exists(f):
            return f
    sys.exit("Font tidak ditemukan. Pakai --font /path/ke/font-bold.ttf")


def ff_path(p: str) -> str:
    """Escape path untuk dipakai di dalam filtergraph ffmpeg."""
    return p.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def probe_size(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "csv=p=0", path,
    ], text=True).strip()
    w, h = out.split(",")[:2]
    return int(w), int(h)


def main():
    ap = argparse.ArgumentParser(description="Klip 9:16 kampanye SkiiMaskTimmy")
    ap.add_argument("--input", required=True, help="File VOD/rekaman stream Timmy")
    ap.add_argument("--start", required=True, help="Waktu mulai, mis. 01:23:45")
    ap.add_argument("--end", required=True, help="Waktu selesai, mis. 01:24:12")
    ap.add_argument("--facecam", required=True,
                    help="Area facecam di video asli: x,y,lebar,tinggi (piksel)")
    ap.add_argument("--game", default=None,
                    help="Area gameplay x,y,lebar,tinggi (default: tengah layar)")
    ap.add_argument("--hook", default="", help="Teks hook di awal (bahasa Inggris)")
    ap.add_argument("--hook-seconds", type=float, default=0,
                    help="Lama hook tampil (0 = sepanjang video)")
    ap.add_argument("--overlay", default=None,
                    help="PNG overlay Twitch dari Drive kampanye (transparan)")
    ap.add_argument("--subs", default=None, help="File .srt subtitle (opsional)")
    ap.add_argument("--font", default=None)
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg belum terpasang.")

    dur = to_seconds(a.end) - to_seconds(a.start)
    if dur < MIN_SECONDS:
        sys.exit(f"Durasi {dur:.1f}s. Kampanye mewajibkan minimal {MIN_SECONDS} detik.")

    src_w, src_h = probe_size(a.input)
    fx, fy, fw, fh = [int(v) for v in a.facecam.split(",")]

    if a.game:
        gx, gy, gw, gh = [int(v) for v in a.game.split(",")]
    else:
        # potong tengah dengan rasio area gameplay (1080:1200)
        gh = src_h
        gw = int(round(gh * W / GAME_H))
        gw = min(gw, src_w)
        gx, gy = (src_w - gw) // 2, 0

    font = ff_path(find_font(a.font))
    tmp = tempfile.mkdtemp()

    handle_file = os.path.join(tmp, "handle.txt")
    with open(handle_file, "w") as f:
        f.write(HANDLE)

    parts = [
        # facecam: isi penuh lebar, potong supaya pas 1080x720
        f"[0:v]crop={fw}:{fh}:{fx}:{fy},scale={W}:{CAM_H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{CAM_H},setsar=1[cam]",
        f"[0:v]crop={gw}:{gh}:{gx}:{gy},scale={W}:{GAME_H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{GAME_H},setsar=1[game]",
        "[cam][game]vstack=inputs=2,"
        f"drawbox=x=0:y={CAM_H - 3}:w={W}:h=6:color=white@0.9:t=fill[base]",
    ]
    last = "base"

    if a.overlay:
        parts.append(f"[1:v]scale={W}:{H}[ov]")
        parts.append(f"[{last}][ov]overlay=0:0:format=auto[withov]")
        last = "withov"

    if a.subs:
        parts.append(
            f"[{last}]subtitles='{ff_path(a.subs)}':force_style="
            "'FontName=Arial,FontSize=14,Bold=1,PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,BorderStyle=1,Outline=3,Alignment=2,MarginV=170'[subbed]"
        )
        last = "subbed"

    if a.hook:
        hook_file = os.path.join(tmp, "hook.txt")
        with open(hook_file, "w") as f:
            f.write("\n".join(textwrap.wrap(a.hook.upper(), 18)))
        enable = f":enable='lt(t,{a.hook_seconds})'" if a.hook_seconds > 0 else ""
        parts.append(
            f"[{last}]drawtext=fontfile='{font}':textfile='{ff_path(hook_file)}':"
            "fontsize=74:fontcolor=white:line_spacing=10:"
            "box=1:boxcolor=black@0.75:boxborderw=24:"
            f"x=(w-text_w)/2:y={CAM_H + 60}{enable}[hooked]"
        )
        last = "hooked"

    # handle Twitch: wajib tampil sepanjang video
    parts.append(
        f"[{last}]drawtext=fontfile='{font}':textfile='{ff_path(handle_file)}':"
        "fontsize=58:fontcolor=white:box=1:boxcolor=0x9146FF@0.92:boxborderw=20:"
        f"x=(w-text_w)/2:y=h-text_h-90,fps={a.fps},format=yuv420p[v]"
    )

    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats",
           "-ss", a.start, "-to", a.end, "-i", a.input]
    if a.overlay:
        cmd += ["-loop", "1", "-i", a.overlay]
    cmd += [
        "-filter_complex", ";".join(parts),
        "-map", "[v]", "-map", "0:a?",
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",   # suara Timmy jelas, tanpa musik
        "-t", f"{dur}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", a.output,
    ]
    subprocess.run(cmd, check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\nSelesai: {a.output} ({dur:.1f} detik, {W}x{H})")
    if not a.overlay:
        print("PERINGATAN: belum pakai --overlay. Overlay Twitch WAJIB untuk kampanye ini.")


if __name__ == "__main__":
    main()
