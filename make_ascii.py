"""Turns a photo into coloured ASCII art (ascii.json). Run once, locally:

    pip install pillow
    python make_ascii.py photo.jpg
"""
import colorsys
import json
import sys

from PIL import Image, ImageFilter, ImageOps

WIDTH = 104         # characters
CHAR_RATIO = 2.08   # a character is about twice as tall as it is wide
RAMP = "@%#*+=-:. "  # dark pixel -> dense character


def is_background(r, g, b):
    return b > 140 and b > r + 45  # plain blue photo background


def main(path, crop=(50, 15, 350, 345)):
    img = Image.open(path).convert("RGB").resize((400, 400)).crop(crop)
    height = round(WIDTH * img.height / img.width / CHAR_RATIO)
    small = img.resize((WIDTH, height), Image.LANCZOS)
    mask = Image.new("L", small.size, 0)
    for y in range(height):
        for x in range(WIDTH):
            mask.putpixel((x, y), 0 if is_background(*small.getpixel((x, y))) else 255)
    gray = ImageOps.autocontrast(ImageOps.grayscale(small), cutoff=2, mask=mask)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=1, percent=80, threshold=0))
    rows = []
    for y in range(height):
        row = []
        for x in range(WIDTH):
            r, g, b = small.getpixel((x, y))
            if not mask.getpixel((x, y)):
                row.append([" ", " ", None])
                continue
            v = gray.getpixel((x, y)) / 255
            # dark theme: bright pixels get dense characters; light theme: the reverse
            dark = RAMP[min(int((1 - v) * len(RAMP)), len(RAMP) - 1)]
            light = RAMP[min(int(v * len(RAMP)), len(RAMP) - 1)]
            h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            if l < 0.3:
                s *= 0.25  # remove the blue tint from dark hair
            colour = "#%02x%02x%02x" % tuple(int(c * 255) for c in colorsys.hls_to_rgb(h, l, s))
            row.append([dark, light, colour])
        rows.append(row)
    with open("ascii.json", "w") as f:
        json.dump(rows, f, separators=(",", ":"))


if __name__ == "__main__":
    main(sys.argv[1])
