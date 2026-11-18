"""Kan-chan's eyes: the webcam, faces, and the people she knows by sight.

Everything here runs on this PC. No photo is ever saved: for each person who has been
introduced she keeps only a face fingerprint (a list of numbers that can't be turned back into
a picture) and a short note of how they looked, both in the same file as her other notes.
Faces of people nobody introduced are ignored and never stored.

No Qt in here, so it can be tested without a screen.
"""
import base64
import datetime
import glob
import json
import os
import re

os.environ.setdefault("OPENCV_LOG_LEVEL", "ERROR")
try:
    import cv2
    import numpy as np
except ImportError:          # the eyes are optional; the rest of Kan-chan works without them
    cv2 = np = None

HERE = os.path.dirname(os.path.abspath(__file__))
MODELS = os.environ.get("KANTAN_KANCHAN_VISION", os.path.join(HERE, "vision"))
DETECT = os.path.join(MODELS, "face_detection_yunet_2023mar.onnx")
RECOGNISE = os.path.join(MODELS, "face_recognition_sface_2021dec.onnx")
SAME = 0.40                  # cosine similarity to count as the same person (SFace suggests 0.363)
SAMPLES = 12                 # face fingerprints kept per person (several angles and lights)


def available():
    return cv2 is not None and os.path.exists(DETECT) and os.path.exists(RECOGNISE)


def has_camera():
    return bool(os.environ.get("KANTAN_KANCHAN_CAMERA")) or bool(glob.glob("/dev/video*"))


class Camera:
    """The webcam, opened only while she's allowed to see. KANTAN_KANCHAN_CAMERA can point at an
    image file (read again on every look, so a test can swap it) or a folder of images (one per
    look, in turn) instead of a real camera."""

    def __init__(self):
        self.fake = os.environ.get("KANTAN_KANCHAN_CAMERA")
        self.cap = None
        self.i = 0

    def open(self):
        if self.fake:
            return True
        for index in range(4):
            cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                ok, _ = cap.read()
                if ok:
                    self.cap = cap
                    return True
            cap.release()
        return False

    def grab(self):
        if self.fake:
            if os.path.isdir(self.fake):
                files = sorted(glob.glob(os.path.join(self.fake, "*.jpg")) + glob.glob(os.path.join(self.fake, "*.png")))
                if not files:
                    return None
                path = files[self.i % len(files)]
                self.i += 1
            else:
                path = self.fake
            return cv2.imread(path) if os.path.exists(path) else None
        if not self.cap:
            return None
        for _ in range(2):           # drop a stale buffered frame
            ok, frame = self.cap.read()
        return frame if ok else None

    def close(self):
        if self.cap:
            self.cap.release()
            self.cap = None


class Faces:
    """Find faces in a picture and make a fingerprint of each (OpenCV YuNet + SFace)."""

    def __init__(self):
        self.detector = cv2.FaceDetectorYN.create(DETECT, "", (320, 320), 0.8, 0.3, 50)
        self.recogniser = cv2.FaceRecognizerSF.create(RECOGNISE, "")

    def find(self, frame, min_size=60):
        """Faces, biggest (nearest) first: [{"box": (x, y, w, h), "feature": array}]."""
        h, w = frame.shape[:2]
        scale = min(1.0, 960 / max(w, h))
        small = cv2.resize(frame, (int(w * scale), int(h * scale))) if scale < 1 else frame
        self.detector.setInputSize((small.shape[1], small.shape[0]))
        _, found = self.detector.detect(small)
        faces = []
        for row in (found if found is not None else []):
            row = row.copy()
            row[:14] /= scale
            x, y, fw, fh = (int(v) for v in row[:4])
            if min(fw, fh) < min_size:
                continue                       # too far away to tell who it is
            aligned = self.recogniser.alignCrop(frame, row)
            feature = self.recogniser.feature(aligned).flatten().astype("float32")
            faces.append({"box": (x, y, fw, fh), "feature": feature / (np.linalg.norm(feature) or 1)})
        faces.sort(key=lambda f: f["box"][2] * f["box"][3], reverse=True)
        return faces


def head_and_shoulders(frame, box):
    """The part of the picture around a face, for describing how someone looks (JPEG bytes)."""
    x, y, w, h = box
    H, W = frame.shape[:2]
    x0, x1 = max(0, x - w), min(W, x + 2 * w)
    y0, y1 = max(0, y - int(h * 0.8)), min(H, y + int(h * 2.2))
    crop = frame[y0:y1, x0:x1]
    if max(crop.shape[:2]) > 512:
        s = 512 / max(crop.shape[:2])
        crop = cv2.resize(crop, (int(crop.shape[1] * s), int(crop.shape[0] * s)))
    ok, jpg = cv2.imencode(".jpg", crop, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return jpg.tobytes() if ok else None


class People:
    """The people she knows by sight, in the same SQLite file as her notes."""

    def __init__(self, db):
        self.db = db
        db.execute("""CREATE TABLE IF NOT EXISTS people (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, look TEXT, look_date TEXT,
            created TEXT NOT NULL, seen TEXT)""")
        db.execute("""CREATE TABLE IF NOT EXISTS faces (
            id INTEGER PRIMARY KEY, person INTEGER NOT NULL, feature BLOB NOT NULL, created TEXT NOT NULL)""")
        db.commit()

    @staticmethod
    def _now():
        return datetime.datetime.now().isoformat(timespec="seconds")

    def all(self):
        rows = self.db.execute("""SELECT p.*, (SELECT COUNT(*) FROM faces f WHERE f.person = p.id) AS samples
                                  FROM people p ORDER BY name""")
        return [dict(r) for r in rows]

    def get(self, pid):
        r = self.db.execute("SELECT * FROM people WHERE id = ?", (pid,)).fetchone()
        return dict(r) if r else None

    def by_name(self, name):
        r = self.db.execute("SELECT * FROM people WHERE lower(name) = lower(?)", (name.strip(),)).fetchone()
        return dict(r) if r else None

    def add(self, name):
        same = self.by_name(name)
        if same:
            return same["id"]
        cur = self.db.execute("INSERT INTO people (name, created) VALUES (?, ?)", (name.strip()[:60], self._now()))
        self.db.commit()
        return cur.lastrowid

    def add_face(self, pid, feature):
        self.db.execute("INSERT INTO faces (person, feature, created) VALUES (?, ?, ?)",
                        (pid, feature.astype("float32").tobytes(), self._now()))
        extra = self.db.execute("SELECT id FROM faces WHERE person = ? ORDER BY id DESC LIMIT -1 OFFSET ?",
                                (pid, SAMPLES)).fetchall()
        for r in extra:                                    # keep the newest few
            self.db.execute("DELETE FROM faces WHERE id = ?", (r["id"],))
        self.db.commit()

    def rename(self, pid, name):
        self.db.execute("UPDATE people SET name = ? WHERE id = ?", (name.strip()[:60], pid))
        self.db.commit()

    def delete(self, pid):
        self.db.execute("DELETE FROM faces WHERE person = ?", (pid,))
        self.db.execute("DELETE FROM people WHERE id = ?", (pid,))
        self.db.commit()

    def clear(self):
        self.db.execute("DELETE FROM faces")
        self.db.execute("DELETE FROM people")
        self.db.commit()

    def set_look(self, pid, look):
        self.db.execute("UPDATE people SET look = ?, look_date = ? WHERE id = ?", (look, self._now(), pid))
        self.db.commit()

    def saw(self, pid):
        self.db.execute("UPDATE people SET seen = ? WHERE id = ?", (self._now(), pid))
        self.db.commit()

    def match(self, feature):
        """(person id, similarity) of the best match, or (None, best similarity)."""
        best, who = 0.0, None
        for r in self.db.execute("SELECT person, feature FROM faces"):
            sim = float(np.dot(feature, np.frombuffer(r["feature"], dtype="float32")))
            if sim > best:
                best, who = sim, r["person"]
        return (who, best) if best >= SAME else (None, best)


# ---- describing how someone looks (local AI only) -------------------------------------------

LOOK_PROMPT = (
    "Describe the visible appearance of the main person in this picture for a friend who will "
    "see them again later. Only these things: hair (colour, length, style, or bald), glasses or "
    "not, hat or not, and the colour of their top. Plain neutral words. Never mention body, "
    "weight, skin, age, face shape, health, expression or anything else. Reply with JSON only: "
    '{"hair": "...", "glasses": "...", "hat": "...", "top": "..."}')

CHANGE_PROMPT = (
    "Two notes describe the same person's hair and glasses at two different times, written from "
    "camera pictures (so wording, lighting and colour shades vary). Did something clearly and "
    "really change: a new hair colour, a much shorter or longer cut, a different style such as "
    "tied up versus down, or glasses on versus off? Differences in wording, a lighter or darker "
    "shade of the same colour, or one note giving more detail are NOT a change, and greying, "
    "thinning or receding hair never counts (that is about age). When unsure, it didn't change. Reply with JSON only: {\"changed\": true or false, \"what\": \"a few friendly "
    "words about the change, said to them, such as 'your hair is much shorter', or empty\"}\n\nBefore: %s\nNow: %s")


def _post(url, body, headers=None, timeout=120):
    import urllib.request
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _ask(ep, prompt, jpg=None, timeout=120):
    """One question to the AI, with a picture if given. Returns the parsed JSON (or {})."""
    if ep["kind"] == "openai":
        content = [{"type": "text", "text": prompt}]
        if jpg:
            content.append({"type": "image_url", "image_url":
                            {"url": "data:image/jpeg;base64," + base64.b64encode(jpg).decode()}})
        body = {"model": ep["model"], "temperature": 0.1, "messages": [{"role": "user", "content": content}]}
        r = _post(ep["url"] + "/chat/completions", body,
                  {"Authorization": "Bearer " + ep["key"]} if ep.get("key") else None, timeout)
        text = r["choices"][0]["message"]["content"]
    else:
        msg = {"role": "user", "content": prompt}
        if jpg:
            msg["images"] = [base64.b64encode(jpg).decode()]
        body = {"model": ep["model"], "messages": [msg], "stream": False, "format": "json",
                "options": {"temperature": 0.1}}
        text = _post(ep["url"] + "/api/chat", body, timeout=timeout)["message"]["content"]
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        return json.loads(m.group(0)) if m else {}
    except ValueError:
        return {}


BANNED = re.compile(r"(?i)\b(fat|thin|skinny|slim|overweight|weight|chubby|wrinkl|acne|spot|skin|pale|tan(ned)?|"
                    r"old|young|aged|tired|sick|ill|healthy|pretty|ugly|attractive|bald(ing)? patch|scar)\w*")


AGE = re.compile(r"(?i)(grey|gray|silver|white|thinning|receding|bald)")


def describe(ep, jpg):
    """A short note of how someone looks: hair, glasses, hat, top. None if the AI can't see."""
    ans = _ask(ep, LOOK_PROMPT, jpg)
    parts = []
    for key in ("hair", "glasses", "hat", "top"):
        v = re.sub(r"\s+", " ", str(ans.get(key) or "")).strip().rstrip(".")[:60]
        if v and not BANNED.search(v):
            parts.append(f"{key}: {v}")
    return "; ".join(parts) or None


def hair_and_glasses(look):
    return "; ".join(p for p in (look or "").split("; ") if p.startswith(("hair:", "glasses:")))


def changed(ep, before, now):
    """What clearly changed in someone's hair or glasses since last time ("" if nothing)."""
    a, b = hair_and_glasses(before), hair_and_glasses(now)
    if not a or not b or a == b:
        return ""
    ans = _ask(ep, CHANGE_PROMPT % (a, b))
    if ans.get("changed") is True:
        what = re.sub(r"\s+", " ", str(ans.get("what") or "")).strip()[:100]
        return "" if BANNED.search(what) or AGE.search(what) else (what or "their hair or glasses look different")
    return ""


def scene(people, me_name=""):
    """What she can see, as a few lines for her instructions (no pictures, just names).
    people: [{"name", "change"}] for introduced people in view, plus {"name": None} for others."""
    known = [p for p in people if p.get("name")]
    strangers = len(people) - len(known)
    if not people:
        return ""
    lines = ["What you can see through the webcam right now (the person allowed it; you can see only "
             "while your window is open):"]
    for i, p in enumerate(known):
        near = " (nearest the screen, so probably the one talking to you)" if i == 0 and people[0] is p else ""
        line = f"- {p['name']} is here{near}."
        if p.get("change"):
            line += (f" Since you last saw {p['name']}: {p['change']}. You may mention it once, kindly and "
                     "briefly, if it fits (for example \"Oh, you changed your hair!\").")
        lines.append(line)
    if strangers:
        lines.append(f"- {strangers} {'person' if strangers == 1 else 'people'} you haven't been introduced to. "
                     "Don't guess who they are or describe them. You may say hello, and the person can "
                     "introduce them to you with the \"Introduce someone\" button.")
    lines.append("Never comment on anyone's body, weight, skin, age or health. Don't describe what you "
                 "see unless asked.")
    return "\n".join(lines)
