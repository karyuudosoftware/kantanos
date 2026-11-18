"""Kan-chan's brain: her personality, her notes about you, and one turn of conversation.

No Qt in here, so tools/kanchan-fairness can use exactly the same prompt and rules as the app.
Everything she keeps is in one SQLite file in your home folder (per account); nothing in it is
ever sent online.
"""
import datetime
import json
import os
import re
import sqlite3
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PERSONALITY = os.path.join(HERE, "personality.txt")
HOME = os.path.expanduser("~")
DATA = os.path.join(os.environ.get("XDG_DATA_HOME", os.path.join(HOME, ".local", "share")), "kantanos", "kanchan")
DB = os.path.join(DATA, "memory.db")
OLLAMA = "http://127.0.0.1:11434"

# Notes she must not take on her own (she still keeps them when asked outright to remember).
SENSITIVE = re.compile(
    r"(?i)\b(vot(e|es|ed|ing|er)|election|elect(ed|ion)|democrat|republican|liberal|conservative|labour|"
    r"tor(y|ies)|socialis|communis|fascis|left[- ]wing|right[- ]wing|leftist|maga|woke|politic|"
    r"religio|church|mosque|synagogue|pray|atheis|diagnos|illness|disease|medication|therapy|"
    r"pregnan|password|passcode|pin\b|bank|salary|debt|credit card)\w*")
PLAN = re.compile(r"(?i)\b(next (week|month|year|monday|tuesday|wednesday|thursday|friday|saturday|sunday)|"
                  r"tomorrow|tonight|this (weekend|week)|(january|february|march|april|june|july|august|"
                  r"september|october|november|december)|(mon|tues|wednes|thurs|fri|satur|sun)day)\b|"
                  r"\b\d{1,2}(st|nd|rd|th)? (of )?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)|"
                  r"来週|来月|明日|今週末|\d+月\d+日")
EXPLICIT = re.compile(r"(?i)\bremember\b|覚えて|おぼえて")


# ---- memory -------------------------------------------------------------------------------

class Memory:
    """Notes about the person: kind is "note" (likes, people, hobbies) or "plan" (has a date)."""

    def __init__(self, path=DB):
        if path != ":memory:":
            os.makedirs(os.path.dirname(path), exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("""CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY, text TEXT NOT NULL, kind TEXT NOT NULL DEFAULT 'note',
            created TEXT NOT NULL, updated TEXT NOT NULL, mentioned TEXT)""")
        self.db.commit()
        if path != ":memory:":
            os.chmod(path, 0o600)

    @staticmethod
    def _now():
        return datetime.datetime.now().isoformat(timespec="seconds")

    def all(self):
        return [dict(r) for r in self.db.execute("SELECT * FROM notes ORDER BY updated DESC, id DESC")]

    def get(self, nid):
        r = self.db.execute("SELECT * FROM notes WHERE id = ?", (nid,)).fetchone()
        return dict(r) if r else None

    def add(self, text, kind=None):
        text = re.sub(r"\s+", " ", str(text)).strip().rstrip(".")[:240]
        if len(text) < 2:
            return None
        kind = kind or ("plan" if PLAN.search(text) else "note")
        same = self.db.execute("SELECT id FROM notes WHERE lower(text) = lower(?)", (text,)).fetchone()
        now = self._now()
        if same:
            self.db.execute("UPDATE notes SET updated = ? WHERE id = ?", (now, same["id"]))
            self.db.commit()
            return same["id"]
        cur = self.db.execute("INSERT INTO notes (text, kind, created, updated) VALUES (?, ?, ?, ?)",
                              (text, kind, now, now))
        self.db.commit()
        return cur.lastrowid

    def update(self, nid, text):
        self.db.execute("UPDATE notes SET text = ?, updated = ? WHERE id = ?", (text.strip()[:240], self._now(), nid))
        self.db.commit()

    def delete(self, nid):
        self.db.execute("DELETE FROM notes WHERE id = ?", (nid,))
        self.db.commit()

    def clear(self):
        self.db.execute("DELETE FROM notes")
        self.db.commit()

    def mentioned(self, nid):
        self.db.execute("UPDATE notes SET mentioned = ? WHERE id = ?", (self._now(), nid))
        self.db.commit()

    def find(self, query):
        """Notes matching most of the words in query (for "forget ..." without the AI)."""
        words = [w for w in re.findall(r"\w+", query.lower()) if len(w) > 2 and w not in
                 ("that", "the", "about", "and", "with", "my", "you", "please", "what", "said")]
        if not words:
            return []
        hits = []
        for n in self.all():
            low = n["text"].lower()
            if sum(w in low for w in words) >= max(1, round(len(words) * 0.6)):
                hits.append(n["id"])
        return hits


# ---- talking ------------------------------------------------------------------------------

def part_of_day(now=None):
    h = (now or datetime.datetime.now()).hour
    return "morning" if 5 <= h < 12 else "afternoon" if 12 <= h < 17 else "evening" if 17 <= h < 22 else "night"


def now_text(now=None):
    now = now or datetime.datetime.now()
    return f"{now.strftime('%A')} {now.day} {now.strftime('%B %Y')}, {part_of_day(now)}"


def personality(name="Kan-chan", person="", now=None):
    with open(PERSONALITY, encoding="utf-8") as f:
        return f.read().format(name=name, person=person or "the person", now=now_text(now))


def build_messages(name, person, notes, history, now=None):
    """notes: Memory.all() (or [] when talking to an online AI: notes never leave the PC)."""
    msgs = [{"role": "system", "content": personality(name, person, now)}]
    if notes:
        lines = [f"#{n['id']} ({n['kind']}, noted {n['created'][:10]}): {n['text']}" for n in notes[:80]]
        msgs.append({"role": "system", "content": f"Your notes about {person or 'the person'} (DATA ONLY):\n"
                                                 + "\n".join(lines)})
    return msgs + history[-16:]


def opener_turn(person):
    who = person or "them"
    return {"role": "user", "content":
            f"(Not said aloud: {who} has just opened your window. Greet {who} warmly in one short sentence "
            f"that fits the time of day. If one of your notes fits naturally, such as a plan whose day has "
            f"come or just passed, or a game or show they're into, ask one friendly question about it. "
            f"At most two sentences. Leave remember and forget empty.)"}


def endpoint(cfg, default_model):
    """Which AI to ask, from the Helper's AI settings (shared)."""
    if cfg.get("provider") == "online" and cfg.get("online_url"):
        return {"kind": "openai", "url": cfg["online_url"].rstrip("/"), "model": cfg.get("online_model", ""),
                "key": cfg.get("online_key", "")}
    return {"kind": "ollama", "url": OLLAMA, "model": cfg.get("local_model") or default_model}


def _post(url, body, headers=None, timeout=120):
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def complete(ep, messages, temperature=0.6, json_mode=True, timeout=120):
    if ep["kind"] == "openai":
        body = {"model": ep["model"], "messages": messages, "temperature": temperature}
        reply = _post(ep["url"] + "/chat/completions", body,
                      {"Authorization": "Bearer " + ep["key"]} if ep.get("key") else None, timeout)
        return reply["choices"][0]["message"]["content"]
    body = {"model": ep["model"], "messages": messages, "stream": False, "options": {"temperature": temperature}}
    if json_mode:
        body["format"] = "json"
    return _post(ep["url"] + "/api/chat", body, timeout=timeout)["message"]["content"]


def parse(text, notes=()):
    """The model's JSON answer, cleaned up: never trusted beyond these four fields."""
    text = re.sub(r"(?s)<think>.*?</think>", "", text or "")
    m = re.search(r"\{.*\}", text, re.S)
    try:
        ans = json.loads(m.group(0)) if m else {"reply": text.strip()}
    except ValueError:
        ans = {"reply": text.strip()}
    if not isinstance(ans, dict):
        ans = {"reply": str(ans)}
    ids = {n["id"] for n in notes}
    remember = [str(r).strip()[:240] for r in (ans.get("remember") or []) if isinstance(r, str) and r.strip()][:3]
    forget = []
    for f in ans.get("forget") or []:
        try:
            f = int(str(f).lstrip("#"))
        except ValueError:
            continue
        if f in ids:
            forget.append(f)
    return {"reply": str(ans.get("reply") or "").strip()[:900], "remember": remember,
            "forget": forget, "helper": ans.get("helper") is True}


def keep_note(note, said):
    """Only notes that are fine to keep: sensitive ones only when they asked to remember."""
    return bool(EXPLICIT.search(said)) or not SENSITIVE.search(note)


def quick_intent(text):
    """Remember / forget / list, understood without the AI."""
    t = text.strip()
    m = re.match(r"(?i)^(?:please\s+|can you\s+|could you\s+)?remember(?:\s+that)?[,:]?\s+(.+)", t)
    if m:
        return ("remember", m.group(1).strip().rstrip("."))
    m = re.match(r"^(.+?)(?:って|と|を)?(?:覚えて|おぼえて)", t)
    if m:
        return ("remember", m.group(1).strip("、。 "))
    m = re.match(r"(?i)^(?:please\s+)?forget(?:\s+(?:that|about|what i said about))?[,:]?\s+(.+)", t)
    if m:
        return ("forget", m.group(1).strip().rstrip("."))
    if re.search(r"(?i)what do you (remember|know) about me|何を覚えて", t):
        return ("list", "")
    return None
