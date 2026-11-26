"""Kan-chan art: her icons, cropped from her head in the current looks.

  python make_icons.py <system_files dir>

- the app icon (Kan-chan app, its notifications): usr/share/icons/hicolor/<n>x<n>/apps/kantanos-kanchan.png,
  from the everyday look
- the Helper's pop-up when something went wrong: usr/share/kantanos/helper/kanchan-worried.png,
  her worried face in the doctor look
"""
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SIZES = (16, 22, 24, 32, 48, 64, 128, 256, 512)


def head(pack, look, frame, spec):
    """A square around her head (face box grown to take in her hair), transparent around her."""
    im = Image.open(os.path.join(pack, "looks", look, frame + ".png")).convert("RGBA")
    fx0, fy0, fx1, fy1 = spec["face"]
    fw, fh = fx1 - fx0, fy1 - fy0
    x0, x1 = fx0 - fw * 0.38, fx1 + fw * 0.38
    y0, y1 = fy0 - fh * 0.55, fy1 + fh * 0.32
    side = max(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    box = (round(cx - side / 2), round(cy - side / 2), round(cx + side / 2), round(cy + side / 2))
    return im.crop(box)


def main():
    root = sys.argv[1]
    pack = os.path.join(root, "usr/share/kantanos/helper/characters/kan-chan")
    looks = json.load(open(os.path.join(HERE, "looks.json"), encoding="utf-8"))
    app = head(pack, "everyday", "idle", looks["everyday"])
    for n in SIZES:
        d = os.path.join(root, f"usr/share/icons/hicolor/{n}x{n}/apps")
        os.makedirs(d, exist_ok=True)
        app.resize((n, n), Image.LANCZOS).save(os.path.join(d, "kantanos-kanchan.png"), optimize=True)
    worried = head(pack, "doctor", "worried", looks["doctor"])
    worried.resize((256, 256), Image.LANCZOS).save(os.path.join(root, "usr/share/kantanos/helper/kanchan-worried.png"),
                                                     optimize=True)
    print("icons written")


if __name__ == "__main__":
    main()
