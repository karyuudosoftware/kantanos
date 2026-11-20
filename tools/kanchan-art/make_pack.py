"""Kan-chan art: build her character pack from the owner's drawings.

For every look in looks.json: cut the drawing out (cutout.py), frame it, then make her other
frames by asking the picture model on this PC (FLUX.2 klein, painter.py) to change only her
face, and paste just the face back onto the drawing so nothing else moves between frames.

  python3 make_pack.py <pack dir> [look ...] [--paste] [--again]
      --paste  only paste the faces again (after changing face/eyes/mouth boxes in looks.json)
      --again  make every frame again with the picture model

Writes <pack>/looks/<look>/{idle,blink,talk1,talk2,think,happy,worried,listen}.png
"""
import json
import os
import sys
import time

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.environ.get("KANTAN_AI_DIR", "/usr/share/kantanos/ai"))
import cutout  # noqa: E402
import painter  # noqa: E402

KEEP = (" Change only her face. Keep everything else exactly the same: the same drawing style, "
        "pose, hair, glasses, clothes, colours, background and framing.")
FACES = {
    "blink": "Her eyes are closed in a relaxed blink, with the same gentle smile.",
    "talk1": "Her mouth is open as if saying 'ah' in the middle of a sentence, eyes open and friendly.",
    "talk2": "Her mouth is only slightly open, as if between words, eyes open and friendly.",
    "think": "She looks thoughtful: eyes glancing up and to the side, mouth closed in a small curious line.",
    "happy": "She is delighted: a big smile, eyes closed in happy upward curves.",
    "worried": "She looks concerned and caring: eyebrows raised in the middle, a small worried mouth.",
    "listen": "She is listening attentively: eyes wide open and bright, mouth closed in a soft smile.",
}


REGION = {"blink": "eyes", "talk1": "mouth", "talk2": "mouth"}


def face_mask(size, box, feather=14):
    m = Image.new("L", size, 0)
    m.paste(255, (box[0] + feather, box[1] + feather, box[2] - feather, box[3] - feather))
    return m.filter(ImageFilter.GaussianBlur(feather / 2))


def on_white(img):
    bg = Image.new("RGB", img.size, "white")
    bg.paste(img, mask=img.getchannel("A"))
    return bg


def main():
    pack = sys.argv[1]
    looks = json.load(open(os.path.join(HERE, "looks.json"), encoding="utf-8"))
    wanted = [a for a in sys.argv[2:] if not a.startswith("--")] or [k for k in looks if not k.startswith("_")]
    for name in wanted:
        spec = looks[name]
        out = os.path.join(pack, "looks", name)
        os.makedirs(out, exist_ok=True)
        src = Image.open(os.path.join(HERE, "source", spec["source"]))
        if spec.get("scale", 1) != 1:
            src = src.resize((int(src.width * spec["scale"]), int(src.height * spec["scale"])), Image.LANCZOS)
        base = cutout.frame(cutout.cut(src), spec.get("bust", 0.5), tuple(spec["box"]) if spec.get("box") else None)
        base.save(os.path.join(out, "idle.png"))
        ref = os.path.join(out, ".ref.png")
        on_white(base).save(ref)
        for frame, words in FACES.items():
            dest = os.path.join(out, frame + ".png")
            if os.path.exists(dest) and "--again" not in sys.argv and "--paste" not in sys.argv:
                continue
            raw = os.path.join(out, f".{frame}-raw.png")
            t0 = time.time()
            if not os.path.exists(raw) or "--again" in sys.argv:
                cmd = painter.command(words + KEEP, raw, (480, 608), 7, reference=ref,
                                      cpu=bool(os.environ.get("KANTAN_SD_CPU")))
                painter.run(cmd)
            # a blink only changes the eyes and talking only the mouth, so nothing else flickers
            part = REGION.get(frame, "face")
            mask = face_mask(base.size, spec.get(part) or spec["face"], 10 if part != "face" else 14)
            edited = Image.open(raw).convert("RGB").resize(base.size, Image.LANCZOS)
            merged = on_white(base)
            merged.paste(edited, mask=mask)              # only the face changes
            result = merged.convert("RGBA")
            result.putalpha(base.getchannel("A"))
            result.save(dest)
            print(f"{name}/{frame} {time.time() - t0:.0f}s", flush=True)
        os.remove(ref)


if __name__ == "__main__":
    main()
