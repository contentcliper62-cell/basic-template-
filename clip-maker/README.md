# Clip Maker – Kampanye SkiiMaskTimmy

Membuat klip vertikal 9:16 yang sesuai aturan kampanye ClippedIn secara otomatis:

| Aturan kampanye | Ditangani otomatis |
|---|---|
| Vertikal 9:16, gameplay + facecam | ✅ 1080x1920, facecam besar di atas, gameplay di bawah |
| Facecam Timmy terlihat | ✅ (kamu tentukan area facecam-nya) |
| Teks `twitch.tv/skiimasktimmy` di layar | ✅ tampil sepanjang video |
| Wajib overlay Twitch | ✅ lewat `--overlay` |
| Suara asli stream jelas, tanpa musik | ✅ audio asli, dinormalisasi |
| Minimal 7 detik | ✅ ditolak kalau kurang |

## 1. Pasang yang dibutuhkan
- Python 3
- ffmpeg (Windows: `winget install ffmpeg`, Mac: `brew install ffmpeg`)
- (Opsional) yt-dlp untuk mengunduh VOD: `pip install yt-dlp`

## 2. Ambil footage dari VOD Timmy
Cari momen bagus di https://www.twitch.tv/skiimasktimmy/videos?filter=archives&sort=time,
catat jam mulai dan selesainya, lalu unduh **bagian itu saja**:

```bash
yt-dlp --download-sections "*01:23:30-01:24:30" -o vod.mp4 https://www.twitch.tv/videos/ID_VOD
```

> Jangan ambil dari tab Clips atau dari channel clipping-nya. Aturan kampanye melarang itu.

Unduh juga PNG overlay dari Drive kampanye dan simpan sebagai `overlay.png`.

## 3. Cari posisi facecam
Ambil satu frame dari video:

```bash
ffmpeg -ss 5 -i vod.mp4 -frames:v 1 frame.png
```

Buka `frame.png` di Paint atau Photoshop. Arahkan kursor ke pojok kiri atas facecam lalu
catat **x,y**, kemudian ukur **lebar,tinggi**-nya. Contoh: `1500,40,400,300`.

## 4. Buat klip

```bash
python3 make_clip.py --input vod.mp4 --start 00:00:12 --end 00:00:40 --facecam 1500,40,400,300 --hook "He had 1 HP and a full bag..." --overlay overlay.png --output klip1.mp4
```

Opsi lain:
- `--hook-seconds 3`: hook hanya tampil 3 detik pertama
- `--game x,y,w,h`: atur sendiri area gameplay (default: bagian tengah)
- `--subs subtitle.srt`: tambahkan subtitle
- `--fps 30`: kalau file terlalu besar

## 5. Upload
Caption (bahasa Inggris) **wajib** memuat `twitch.tv/skiimasktimmy`. Contoh:

```
He really clutched a 1v3 with a pistol 😳 Catch him live → twitch.tv/skiimasktimmy
#skiimasktimmy #twitchclips #fps #gaming
```

Komentar dan like harus aktif. Lalu submit lewat Content Rewards.

## Ide hook (taruh di `--hook`)
- `HE HAD 1 HP AND A FULL BAG...`
- `1V3 WITH ONLY A PISTOL`
- `DOES HE MAKE IT OUT?`
- `WORST DEATH OF THE STREAM 💀`
- `"THIS GAME IS COOKED"`
- `CHAT TOLD HIM NOT TO...`
- `THE JUMPSCARE GOT HIM`
- `LAST SECOND EXTRACT`
