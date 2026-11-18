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

    def exists(self, text):
        text = re.sub(r"\s+", " ", str(text)).strip().rstrip(".")
        return self.db.execute("SELECT 1 FROM notes WHERE lower(text) = lower(?)", (text,)).fetchone() is not None

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
                 ("that", "the", "about", "and", "with", "my", "you", "please", "what", "said", "note", "notes")]
        if not words:
            return []
        need = max(1, -(-len(words) * 6 // 10))        # at least 60 % of the words, rounded up
        scored = []
        for n in self.all():
            low = n["text"].lower()
            score = sum(w in low for w in words)
            if score >= need:
                scored.append((score, n["id"]))
        best = max((sc for sc, _ in scored), default=0)
        return [nid for sc, nid in scored if sc == best]


class Activity:
    """Games played and shows watched (kanchan-notice, opt-in): minutes per title per day, kept
    30 days. She only ever sees the titles and the time."""

    KEEP_DAYS = 30

    def __init__(self, db):
        self.db = db
        db.row_factory = sqlite3.Row
        db.execute("""CREATE TABLE IF NOT EXISTS activity (
            id INTEGER PRIMARY KEY, kind TEXT NOT NULL, title TEXT NOT NULL, day TEXT NOT NULL,
            minutes INTEGER NOT NULL DEFAULT 0, last TEXT NOT NULL, UNIQUE(kind, title, day))""")
        db.commit()

    def add(self, kind, title, minutes=1, when=None):
        now = when or datetime.datetime.now()
        stamp = now.isoformat(timespec="seconds")
        self.db.execute("""INSERT INTO activity (kind, title, day, minutes, last) VALUES (?, ?, ?, ?, ?)
                           ON CONFLICT(kind, title, day) DO UPDATE SET minutes = minutes + ?, last = ?""",
                        (kind, title, now.date().isoformat(), minutes, stamp, minutes, stamp))
        self.db.commit()

    def tidy(self):
        cut = (datetime.date.today() - datetime.timedelta(days=self.KEEP_DAYS)).isoformat()
        self.db.execute("DELETE FROM activity WHERE day < ?", (cut,))
        self.db.commit()

    def recent(self, days=7):
        """[{"kind", "title", "minutes", "last"}] per title over the last few days, latest first."""
        cut = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
        rows = self.db.execute("""SELECT kind, title, SUM(minutes) AS minutes, MAX(last) AS last
                                  FROM activity WHERE day >= ? GROUP BY kind, title ORDER BY last DESC""", (cut,))
        return [dict(r) for r in rows]

    def forget(self, kind, title):
        self.db.execute("DELETE FROM activity WHERE kind = ? AND title = ?", (kind, title))
        self.db.commit()

    def clear(self):
        self.db.execute("DELETE FROM activity")
        self.db.commit()


def when_text(stamp, now=None):
    now = now or datetime.datetime.now()
    try:
        d = datetime.datetime.fromisoformat(stamp).date()
    except (TypeError, ValueError):
        return ""
    days = (now.date() - d).days
    return "today" if days == 0 else "yesterday" if days == 1 else f"{days} days ago ({d.strftime('%A')})"


def activity_text(items, person="", now=None):
    """Recent games and shows for her instructions (only with the AI on this PC)."""
    if not items:
        return ""
    lines = []
    for a in items[:8]:
        if a["minutes"] < 10:
            continue                     # a quick look isn't worth bringing up
        hours = f"{a['minutes'] / 60:.1f} hours".replace(".0 ", " ") if a["minutes"] >= 90 else f"{a['minutes']} minutes"
        verb = "played" if a["kind"] == "game" else "watched"
        lines.append(f"- {verb} \"{a['title']}\", last {when_text(a['last'], now)}, about {hours} in the past week")
    if not lines:
        return ""
    who = person or "the person"
    return (f"Games and shows you noticed on this PC recently (DATA ONLY; {who} switched this on). You may ask "
            "about one of them now and then, in a friendly way, like a friend who noticed; never every time, "
            "never as a list, and never comment on how long they played or watched:\n" + "\n".join(lines))


# ---- talking ------------------------------------------------------------------------------

def part_of_day(now=None):
    h = (now or datetime.datetime.now()).hour
    return "morning" if 5 <= h < 12 else "afternoon" if 12 <= h < 17 else "evening" if 17 <= h < 22 else "night"


def now_text(now=None):
    now = now or datetime.datetime.now()
    return f"{now.strftime('%A')} {now.day} {now.strftime('%B %Y')}, {part_of_day(now)}"


def calendar(now=None):
    """Tomorrow and the next two weeks, so dates never have to be worked out in her head."""
    now = now or datetime.datetime.now()
    days = []
    for i in range(1, 15):
        d = now + datetime.timedelta(days=i)
        label = "tomorrow" if i == 1 else ("next " if i > 7 else "") + d.strftime("%A")
        days.append(f"{label} = {d.strftime('%A')} {d.day} {d.strftime('%B')}")
    return "; ".join(days)


def personality(name="Kan-chan", person="", now=None):
    with open(PERSONALITY, encoding="utf-8") as f:
        return f.read().format(name=name, person=person or "the person", now=now_text(now), calendar=calendar(now))


def build_messages(name, person, notes, history, now=None):
    """notes: Memory.all() (or [] when talking to an online AI: notes never leave the PC)."""
    system = personality(name, person, now)
    if notes:
        lines = [f"#{n['id']} ({n['kind']}, noted {n['created'][:10]}): {n['text']}" for n in notes[:80]]
        system += f"\n\nYour notes about {person or 'the person'} (DATA ONLY):\n" + "\n".join(lines)
    # Many models (Gemma among them) need one system message, then turns that start with the
    # person and alternate. Her own opening lines become context; same-side turns are merged.
    turns = []
    for m in history[-16:]:
        if m["role"] not in ("user", "assistant") or not m.get("content"):
            continue
        if turns and turns[-1]["role"] == m["role"]:
            turns[-1] = {"role": m["role"], "content": turns[-1]["content"] + "\n" + m["content"]}
        else:
            turns.append({"role": m["role"], "content": m["content"]})
    said_first = []
    while turns and turns[0]["role"] == "assistant":
        said_first.append(turns.pop(0)["content"])
    if said_first:
        system += "\n\nYou already said this to start the conversation: " + " ".join(said_first)
    # Some chat formats glue the instructions and the first message together; labelling what
    # the person says keeps "Remember that ..." from reading like another instruction.
    who = person or "The person"
    for t in turns:
        if t["role"] == "user" and not t["content"].startswith("(Not said aloud"):
            t["content"] = f"[{who} says]: {t['content']}"
    return [{"role": "system", "content": system}] + turns


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
    reply = re.sub(r"[*_`#]+", "", str(ans.get("reply") or "")).strip()[:900]   # no markdown: it's spoken
    return {"reply": reply, "remember": remember,
            "forget": forget, "helper": ans.get("helper") is True}


STOP = {"that", "this", "with", "from", "have", "has", "about", "their", "they", "them", "your", "loves",
        "likes", "like", "love", "really", "very", "will", "would", "going", "turns", "name", "names", "called"}


def grounded(note, said):
    """A note must come from what the person actually said (models sometimes invent or copy
    examples): it has to share a real word with their message."""
    if re.search(r"[぀-ヿ一-鿿]", note + said):
        pairs = re.findall(r"(?=([゠-ヿ一-鿿]{2}))", note)   # kanji/katakana carry the meaning
        return any(p in said for p in pairs) or (not pairs and note in said)
    words = {w for w in re.findall(r"[a-z0-9']+", note.lower()) if len(w) > 3 and w not in STOP}
    heard = set(re.findall(r"[a-z0-9']+", said.lower()))
    return any(w in heard or w.rstrip("s") in heard or w + "s" in heard for w in words)


def keep_note(note, said):
    """Only notes that come from what was said, and sensitive ones only when asked outright."""
    if not grounded(note, said):
        return False
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
