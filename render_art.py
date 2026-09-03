#!/usr/bin/env python3
"""
portrait.txt -> portrait-light.png / portrait-dark.png

The art is rendered once, at high resolution, then displayed scaled down in
the README. Two files because GitHub serves a different one per colour scheme
via <picture>; both have transparent backgrounds so they sit on the page
cleanly either way.

    pip install pillow
    python render_art.py

CELL_RATIO is char width / line height. Your art was authored at ~0.55, so
that is what reproduces the proportions you saw in your own preview. Rendering
it at GitHub's code-block ratio (0.414) would stretch the face vertically,
which is exactly the problem the image approach avoids.
"""

import glob

from PIL import Image, ImageDraw, ImageFont

ART = "portrait.txt"
FONT_SIZE = 20          # render size; the README scales the result down
CELL_RATIO = 0.55       # char width / line height the art was authored at
PAD = 12

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    "/System/Library/Fonts/Menlo.ttc",
    "C:/Windows/Fonts/consola.ttf",
]

# GitHub's default body text colours, so the art sits with the rest of the page
THEMES = {
    "light": (36, 41, 47),
    "dark": (201, 209, 217),
}


def find_font():
    for p in FONT_CANDIDATES:
        if glob.glob(p):
            return p
    raise SystemExit("no monospace font found")


def render(lines, colour, out):
    font = ImageFont.truetype(find_font(), FONT_SIZE)
    cw = int(round(font.getlength("M")))
    ch = int(round(cw / CELL_RATIO))

    cols = max(len(x) for x in lines)
    w = cols * cw + 2 * PAD
    h = len(lines) * ch + 2 * PAD

    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    asc, desc = font.getmetrics()
    base = int(round((ch - (asc + desc)) / 2))
    for i, line in enumerate(lines):
        d.text((PAD, PAD + i * ch + base), line, font=font, fill=colour + (255,))
    im.save(out)
    return im.size


if __name__ == "__main__":
    lines = open(ART, encoding="utf-8").read().rstrip("\n").split("\n")
    for name, colour in THEMES.items():
        size = render(lines, colour, f"portrait-{name}.png")
        print(f"portrait-{name}.png  {size[0]}x{size[1]}")
