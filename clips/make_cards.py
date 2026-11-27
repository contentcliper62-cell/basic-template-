#!/usr/bin/env python3
"""Build 9:16 end cards and cover images from the official key art and title logo.

  python3 clips/make_cards.py

Reads  clips/refs/keyart_clean.webp  (key art without title)
       clips/refs/title_logo.webp    (white title logo, transparent)
Writes clips/refs/cards/endcard_{sat,tonight,streaming}.png
       clips/refs/cards/cover{1,2,3}_{sat,tonight,streaming}.png
"""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

ROOT = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(ROOT, "refs")
OUT = os.path.join(REFS, "cards")
W, H = 1080, 1920
BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
XBOLD = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
GOLD = (244, 205, 120)
RED = (176, 32, 40)

PHASES = {
    "sat": ("PREMIERES SAT., NOV. 28", "10/9c on Lifetime"),
    "tonight": ("PREMIERES TONIGHT", "10/9c on Lifetime"),
    "streaming": ("STREAMING NOW", "on Lifetime"),
}
HOOKS = {
    1: "Vivica A. Fox + Jackée Harry\nin a Christmas movie?\nI'm seated",
    2: "POV: your Thanksgiving\nweekend plans\njust changed",
    3: "Lifetime Christmas movie\nseason is officially here",
}


def font(path, size):
    return ImageFont.truetype(path, size)


def background(art):
    bg = art.resize((int(art.width * H / art.height), H), Image.LANCZOS)
    x = (bg.width - W) // 2 + 300  # lean toward the cast side
    bg = bg.crop((x, 0, x + W, H)).filter(ImageFilter.GaussianBlur(28))
    return ImageEnhance.Brightness(bg).enhance(0.55).convert("RGBA")


def cast_layer(art, top):
    """Cast crop from the right side of the key art, faded in at the top edge."""
    crop = art.crop((600, 170, 1600, 900))
    crop = crop.resize((W, int(crop.height * W / crop.width)), Image.LANCZOS).convert("RGBA")
    fade = Image.new("L", crop.size, 255)
    d = ImageDraw.Draw(fade)
    for y in range(160):
        d.line([(0, y), (W, y)], fill=int(255 * y / 160))
    crop.putalpha(fade)
    layer = Image.new("RGBA", (W, H))
    layer.alpha_composite(crop, (0, top))
    return layer


def logo(width):
    lg = Image.open(os.path.join(REFS, "title_logo.webp")).convert("RGBA")
    lg = lg.resize((width, int(lg.height * width / lg.width)), Image.LANCZOS)
    glow = Image.new("RGBA", lg.size, (0, 0, 0, 0))
    glow.putalpha(lg.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda a: int(a * 0.8)))
    out = Image.new("RGBA", lg.size)
    out.alpha_composite(glow)
    out.alpha_composite(lg)
    return out


def centered(draw, y, text, fnt, fill, stroke=0, stroke_fill=(0, 0, 0)):
    for line in text.split("\n"):
        w = draw.textlength(line, font=fnt)
        draw.text(((W - w) / 2, y), line, font=fnt, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        y += int(fnt.size * 1.18)
    return y


def date_block(img, y, phase):
    d = ImageDraw.Draw(img)
    l1, l2 = PHASES[phase]
    y = centered(d, y, l1, font(BLACK, 78), (255, 255, 255), 4)
    centered(d, y + 4, l2, font(XBOLD, 70), GOLD, 4)


def endcard(art, phase):
    img = background(art)
    img.alpha_composite(cast_layer(art, 1120))
    lg = logo(700)
    img.alpha_composite(lg, ((W - lg.width) // 2, 110))
    date_block(img, 110 + lg.height + 30, phase)
    return img.convert("RGB")


def cover(art, n, phase):
    img = background(art)
    img.alpha_composite(cast_layer(art, 1150))
    lg = logo(500)
    img.alpha_composite(lg, ((W - lg.width) // 2, 250))
    d = ImageDraw.Draw(img)
    hook_font = font(BLACK, 66)
    lines = HOOKS[n].split("\n")
    lh = int(hook_font.size * 1.2)
    top = 250 + lg.height + 40
    box_w = max(d.textlength(l, font=hook_font) for l in lines) + 80
    d.rounded_rectangle(((W - box_w) / 2, top - 24, (W + box_w) / 2, top + lh * len(lines) + 14),
                        radius=28, fill=RED + (235,))
    centered(d, top, HOOKS[n], hook_font, (255, 255, 255))
    date_block(img, 1560, phase)  # stays inside the 3:4 grid crop (y 240-1680) for its first line
    return img.convert("RGB")


def main():
    os.makedirs(OUT, exist_ok=True)
    art = Image.open(os.path.join(REFS, "keyart_clean.webp")).convert("RGB")
    for phase in PHASES:
        endcard(art, phase).save(os.path.join(OUT, f"endcard_{phase}.png"))
        for n in HOOKS:
            cover(art, n, phase).save(os.path.join(OUT, f"cover{n}_{phase}.png"))
    print("wrote", sorted(os.listdir(OUT)))


if __name__ == "__main__":
    main()
