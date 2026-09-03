#!/usr/bin/env python3
"""
portrait.txt -> portrait-light.png

One image, used in every colour scheme. Because it has to survive GitHub's
dark theme, it is drawn on an OPAQUE white card rather than a transparent
background - dark ink on transparency would be near-invisible there.

    pip install pillow
    python render_art.py

CELL_RATIO is char width / line height. Your art was authored at ~0.55, so
that is what reproduces the proportions from your own preview.
"""

import glob

from PIL import Image, ImageDraw, ImageFont

ART = "portrait.txt"
OUT = "portrait-light.png"

FONT_SIZE = 20          # render size; the README scales the result down
CELL_RATIO = 0.55       # char width / line height the art was authored at
PAD = 28                # white margin around the art, in render pixels
RADIUS = 24             # card corner radius; 0 for square corners

INK = (36, 41, 47)      # GitHub's light-theme body text colour
CARD = (255, 255, 255)  # opaque, so it reads on dark backgrounds too

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "C:/Windows/Fonts/consola.ttf",
]


def find_font():
    for p in FONT_CANDIDATES:
        if glob.glob(p):
            return p
    raise SystemExit("no monospace font found")


def render(lines, out):
    font = ImageFont.truetype(find_font(), FONT_SIZE)
    cw = int(round(font.getlength("M")))
    ch = int(round(cw / CELL_RATIO))

    w = max(len(x) for x in lines) * cw + 2 * PAD
    h = len(lines) * ch + 2 * PAD

    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if RADIUS:
        d.rounded_rectangle((0, 0, w - 1, h - 1), RADIUS, fill=CARD + (255,))
    else:
        d.rectangle((0, 0, w - 1, h - 1), fill=CARD + (255,))

    asc, desc = font.getmetrics()
    base = int(round((ch - (asc + desc)) / 2))
    for i, line in enumerate(lines):
        d.text((PAD, PAD + i * ch + base), line, font=font, fill=INK + (255,))

    im.save(out)
    return im.size


if __name__ == "__main__":
    lines = open(ART, encoding="utf-8").read().rstrip("\n").split("\n")
    print(OUT, "%dx%d" % render(lines, OUT))
