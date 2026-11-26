"""Kan-chan art: full-length pictures of every look, for the Helper window.

Her frames in looks/<look>/ show her from the head to the hips (480x600). This makes
looks/<look>/full/idle.png from the whole drawing (head to shoes), at a higher resolution,
and small face pictures for the other frames (blink, talk1, talk2, think, happy, worried,
listen), taken from the existing frames, so the faces stay exactly as they are and the pack
doesn't double in size. full/faces.json says where each face goes. The Helper puts them
together when it loads a look.

  python make_full.py <pack dir> [look ...]
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cutout  # noqa: E402

FULL_H = 900          # pixels from the top of her hair to her shoes (shown at about 360-450)
SHARPER = 1.5         # the full picture comes from the drawing at 1.5x the frames' scale
FRAMES = ("blink", "talk1", "talk2", "think", "happy", "worried", "listen")
REGION = {"blink": "eyes", "talk1": "mouth", "talk2": "mouth"}


def soft_box(size, box, feather):
    m = Image.new("L", size, 0)
    m.paste(255, (box[0] + feather, box[1] + feather, box[2] - feather, box[3] - feather))
    return m.filter(ImageFilter.GaussianBlur(feather / 2))


def make(pack, name, spec):
    out = os.path.join(pack, "looks", name, "full")
    os.makedirs(out, exist_ok=True)
    src = Image.open(os.path.join(HERE, "source", spec["source"])).convert("RGB")
    s = spec.get("scale", 1)
    small = src.resize((int(src.width * s), int(src.height * s)), Image.LANCZOS)
    cut = cutout.cut(small)
    bx0, by0, bx1, by1 = cutout.frame_box(cut, spec.get("bust", 0.5), tuple(spec["box"]) if spec.get("box") else None)
    # the whole of her, sharper: the drawing at 1.5x, with the cut-out's outline scaled up
    big = src.resize((int(src.width * s * SHARPER), int(src.height * s * SHARPER)), Image.LANCZOS).convert("RGBA")
    # pulled in by a pixel and softened, so no pale rim of the drawing's white paper shows on
    # a dark window
    alpha = cut.getchannel("A").resize(big.size, Image.LANCZOS).filter(ImageFilter.MinFilter(5)) \
        .filter(ImageFilter.GaussianBlur(0.7))
    big.putalpha(alpha)
    ys, xs = np.nonzero(np.asarray(alpha) > 128)
    pad = int((ys.max() - ys.min()) * 0.02)
    cx0, cy0 = max(0, xs.min() - pad), max(0, ys.min() - pad)
    cx1, cy1 = min(big.width, xs.max() + pad), min(big.height, ys.max() + pad)
    z = FULL_H / (cy1 - cy0)
    full = big.crop((cx0, cy0, cx1, cy1)).resize((round((cx1 - cx0) * z), FULL_H), Image.LANCZOS)
    full.save(os.path.join(out, "idle.png"), optimize=True)
    # where the head-to-hips frames sit in the full picture
    fx, fy = (bx0 * SHARPER - cx0) * z, (by0 * SHARPER - cy0) * z
    k = (bx1 - bx0) * SHARPER * z / cutout.W                    # frame pixels -> full pixels
    faces = {}
    for frame in FRAMES:
        path = os.path.join(pack, "looks", name, frame + ".png")
        if not os.path.isfile(path):
            continue
        part = spec.get(REGION.get(frame, "face")) or spec["face"]
        piece = Image.open(path).convert("RGBA").crop(part)
        mask = soft_box(piece.size, (0, 0) + piece.size, 6 if frame in REGION else 10)
        a = np.minimum(np.asarray(mask), np.asarray(piece.getchannel("A")))
        piece.putalpha(Image.fromarray(a.astype(np.uint8)))
        w, h = round(piece.width * k), round(piece.height * k)
        x, y = round(fx + part[0] * k), round(fy + part[1] * k)
        piece.resize((w, h), Image.LANCZOS).save(os.path.join(out, frame + ".png"), optimize=True)
        faces[frame] = [x, y]
    with open(os.path.join(out, "faces.json"), "w", encoding="utf-8") as f:
        json.dump(faces, f, indent=1)
    print(f"{name}: {full.width}x{full.height}, {len(faces)} faces", flush=True)


def main():
    pack = sys.argv[1]
    looks = json.load(open(os.path.join(HERE, "looks.json"), encoding="utf-8"))
    wanted = sys.argv[2:] or [k for k in looks if not k.startswith("_")]
    for name in wanted:
        make(pack, name, looks[name])


if __name__ == "__main__":
    main()
