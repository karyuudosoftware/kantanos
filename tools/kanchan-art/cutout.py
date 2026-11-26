"""Kan-chan art: cut a character drawing out of its white background and frame it for her
window (240x300, drawn here at twice that: 480x600).

  python cutout.py <drawing.jpg> <out.png> [--bust 0.5] [--box left,top,height]

The background is everything white-ish that touches the picture's edge (flood fill), plus
anything not joined to the biggest shape (floating panels, sparkles). --bust is how much of
her height (from the top of her hair) the frame shows.
"""
import sys
from collections import deque

import numpy as np
from PIL import Image, ImageFilter

W, H = 480, 600


def cut(img, tol=28):
    a = np.asarray(img.convert("RGB")).astype(np.int16)
    h, w, _ = a.shape
    white = (a.min(axis=2) > 255 - tol) & ((a.max(axis=2) - a.min(axis=2)) < 22)
    bg = np.zeros((h, w), bool)
    q = deque((y, x) for y in range(h) for x in (0, w - 1) if white[y, x])
    q.extend((y, x) for x in range(w) for y in (0, h - 1) if white[y, x])
    for y, x in q:
        bg[y, x] = True
    while q:
        y, x = q.popleft()
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= ny < h and 0 <= nx < w and not bg[ny, nx] and white[ny, nx]:
                bg[ny, nx] = True
                q.append((ny, nx))
    fg = ~bg
    # keep only the biggest joined shape (the character), drop floating bits
    lab = np.zeros((h, w), np.int32)
    best, best_n, n = 0, 0, 0
    for sy in range(h):
        for sx in range(w):
            if fg[sy, sx] and not lab[sy, sx]:
                n += 1
                lab[sy, sx] = n
                q, size = deque([(sy, sx)]), 0
                while q:
                    y, x = q.popleft()
                    size += 1
                    for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                        if 0 <= ny < h and 0 <= nx < w and fg[ny, nx] and not lab[ny, nx]:
                            lab[ny, nx] = n
                            q.append((ny, nx))
                if size > best_n:
                    best, best_n = n, size
    keep = lab == best
    alpha = Image.fromarray((keep * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))
    out = img.convert("RGBA")
    out.putalpha(alpha)
    return out


def holes(img, cutimg, protect=None, min_size=40):
    """The paper showing through gaps the outline encloses (between an arm and her body,
    under an umbrella): a mask of pixels to make see-through. Only pure, neutral white counts
    (the paper is about 253 grey-free; white clothes are darker and a little blue), and
    nothing inside `protect` (left, top, right, bottom: her head, where the glasses' shine
    and the hair clip are pure white too)."""
    a = np.asarray(img.convert("RGB")).astype(np.int16)
    inside = np.asarray(cutimg.getchannel("A")) > 128
    white = (a.min(axis=2) > 227) & ((a.max(axis=2) - a.min(axis=2)) < 22) & inside
    h, w = white.shape
    out = np.zeros((h, w), bool)
    seen = np.zeros((h, w), bool)
    for sy, sx in zip(*np.nonzero(white)):
        if seen[sy, sx]:
            continue
        seen[sy, sx] = True
        q, pts = deque([(sy, sx)]), []
        while q:
            y, x = q.popleft()
            pts.append((y, x))
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= ny < h and 0 <= nx < w and white[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    q.append((ny, nx))
        if len(pts) < min_size:
            continue
        p = np.array(pts)
        if protect:
            cy, cx = p.mean(axis=0)
            if protect[0] <= cx <= protect[2] and protect[1] <= cy <= protect[3]:
                continue
        m = a[p[:, 0], p[:, 1]].mean(axis=0)
        if m.mean() >= 250 and abs(m[2] - m[0]) < 3:
            out[p[:, 0], p[:, 1]] = True
    return out


def head_box(spec_face, frame_box_):
    """Her face in the cut-out drawing (the frame's face box, given in 480x600 frame pixels).
    A white patch whose middle is in it is the glasses' shine or the hair clip, not paper."""
    bx0, by0, bx1, by1 = frame_box_
    k = (bx1 - bx0) / W
    fx0, fy0, fx1, fy1 = spec_face
    return (int(bx0 + fx0 * k), int(by0 + fy0 * k), int(bx0 + fx1 * k), int(by0 + fy1 * k))


def frame(cutimg, bust=0.5, box=None):
    """Head to chest (or as much of her as --bust says), centred on her head, 480x600.
    box: (left, top, height) in the drawing's own pixels, for pictures where the top of the
    shape isn't her head (an umbrella, a hat)."""
    return cutimg.crop(frame_box(cutimg, bust, box)).resize((W, H), Image.LANCZOS)


def frame_box(cutimg, bust=0.5, box=None):
    """The part of the cut-out drawing that frame() shows: (left, top, right, bottom)."""
    if box:
        left, top, h = box
        return (left, top, left + int(h * W / H), top + h)
    a = np.asarray(cutimg.getchannel("A")) > 128
    ys, xs = np.nonzero(a)
    top, bottom = ys.min(), ys.max()
    height = bottom - top
    head_rows = a[top: top + max(1, int(height * 0.12))]
    hx = int(np.nonzero(head_rows.any(axis=0))[0].mean())      # middle of her head
    crop_h = int(height * bust)
    crop_w = int(crop_h * W / H)
    margin = int(crop_h * 0.06)
    return (hx - crop_w // 2, top - margin, hx - crop_w // 2 + crop_w, top - margin + crop_h)


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    bust = float(sys.argv[sys.argv.index("--bust") + 1]) if "--bust" in sys.argv else 0.5
    box = tuple(int(v) for v in sys.argv[sys.argv.index("--box") + 1].split(",")) if "--box" in sys.argv else None
    frame(cut(Image.open(src)), bust, box).save(dst)
    print("wrote", dst)
