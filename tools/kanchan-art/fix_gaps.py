"""Kan-chan art: make the paper showing through enclosed gaps (between an arm and her body,
under an umbrella) see-through in the head-to-hips frames already in a pack, without making
the frames again. (cutout.holes; new packs get it from make_full.py and this.)

  python fix_gaps.py <pack dir> [look ...]
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cutout  # noqa: E402


def main():
    pack = sys.argv[1]
    looks = json.load(open(os.path.join(HERE, "looks.json"), encoding="utf-8"))
    for name in sys.argv[2:] or [k for k in looks if not k.startswith("_")]:
        spec = looks[name]
        src = Image.open(os.path.join(HERE, "source", spec["source"])).convert("RGB")
        s = spec.get("scale", 1)
        small = src.resize((int(src.width * s), int(src.height * s)), Image.LANCZOS)
        cut = cutout.cut(small)
        box = cutout.frame_box(cut, spec.get("bust", 0.5), tuple(spec["box"]) if spec.get("box") else None)
        gaps = cutout.holes(small, cut, cutout.head_box(spec["face"], box))
        if not gaps.any():
            print(f"{name}: no gaps", flush=True)
            continue
        hole = Image.fromarray((gaps * 255).astype(np.uint8)).crop(box).resize((cutout.W, cutout.H), Image.LANCZOS)
        keep = 255 - np.asarray(hole).astype(np.int16)
        folder = os.path.join(pack, "looks", name)
        for f in sorted(os.listdir(folder)):
            if not f.endswith(".png") or f.startswith("."):
                continue
            im = Image.open(os.path.join(folder, f)).convert("RGBA")
            a = np.minimum(np.asarray(im.getchannel("A")).astype(np.int16), keep)
            im.putalpha(Image.fromarray(a.astype(np.uint8)))
            im.save(os.path.join(folder, f), optimize=True)
        print(f"{name}: {int(gaps.sum())} pixels of paper made see-through", flush=True)


if __name__ == "__main__":
    main()
