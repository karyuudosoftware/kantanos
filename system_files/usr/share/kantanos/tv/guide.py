"""KantanOS Watch TV: the programme guide (EPG).

XMLTV guides (Pluto TV and Plex from i.mjh.nz, the family's own provider's guide) are read into
a small SQLite file, keeping only channels in the lineup and from 3 hours ago to 3 days ahead.
"""
import datetime
import io
import os
import sqlite3
import time
import xml.etree.ElementTree as ET

import lineup

DB = os.path.join(lineup.DATA, "guide.sqlite")
MAX_AGE = 6 * 3600


def connect():
    os.makedirs(lineup.DATA, exist_ok=True)
    db = sqlite3.connect(DB, timeout=30)
    db.execute("pragma journal_mode=wal")
    db.execute("create table if not exists prog (ch text, start int, stop int, title text, sub text, "
               "descr text, cats text, ep text, icon text)")
    db.execute("create index if not exists prog_ch on prog (ch, start)")
    db.execute("create table if not exists meta (k text primary key, v text)")
    return db


def xmltv_time(s):
    s = (s or "").strip()
    try:
        base = datetime.datetime.strptime(s[:14], "%Y%m%d%H%M%S")
    except ValueError:
        return None
    off = s[14:].strip()
    tz = datetime.timezone.utc
    if len(off) == 5 and off[0] in "+-":
        sign = 1 if off[0] == "+" else -1
        tz = datetime.timezone(sign * datetime.timedelta(hours=int(off[1:3]), minutes=int(off[3:5])))
    return int(base.replace(tzinfo=tz).timestamp())


def age():
    try:
        db = connect()
        row = db.execute("select v from meta where k='made'").fetchone()
        return time.time() - float(row[0]) if row else 1e9
    except sqlite3.Error:
        return 1e9


def refresh(lu, force=False, log=print):
    """Reads every guide the lineup needs. Returns the number of programmes kept."""
    if not force and age() < MAX_AGE:
        return None
    wanted = {}                                     # (guide url, id) -> [channel keys]
    for c in lu.channels:
        for ref in c.get("epg") or []:
            if ref and ref[0] and ref[0] != "iptv-org" and ref[1]:
                wanted.setdefault((ref[0], ref[1]), []).append(c["key"])
    urls = sorted({u for u, _ in wanted})
    now = time.time()
    lo, hi = now - 3 * 3600, now + 3 * 86400
    rows = []
    seen = set()                                    # (channel, start): a channel with two guides keeps one copy
    for url in urls:
        try:
            data = lineup.fetch(url, max_age=MAX_AGE, timeout=120)
        except OSError as e:
            log(f"guide {url}: {e}")
            continue
        n = 0
        try:
            for _, el in ET.iterparse(io.BytesIO(data), events=("end",)):
                if el.tag != "programme":
                    if el.tag == "channel":
                        el.clear()
                    continue
                keys = wanted.get((url, el.get("channel")))
                if keys:
                    start, stop = xmltv_time(el.get("start")), xmltv_time(el.get("stop"))
                    if start and stop and stop > lo and start < hi:
                        ep = ""
                        for e in el.findall("episode-num"):
                            if e.get("system") == "onscreen" and e.text:
                                ep = e.text.strip()
                        icon = el.find("icon")
                        cats = ", ".join(c.text.strip() for c in el.findall("category") if c.text)
                        row = (start, stop, (el.findtext("title") or "").strip(), (el.findtext("sub-title") or "").strip(),
                               (el.findtext("desc") or "").strip(), cats, ep, icon.get("src") if icon is not None else "")
                        for k in keys:
                            if (k, start) in seen:
                                continue
                            seen.add((k, start))
                            rows.append((k,) + row)
                            n += 1
                el.clear()
        except ET.ParseError as e:
            log(f"guide {url}: {e}")
        log(f"guide {url.split('/')[2]}: {n} programmes")
    db = connect()
    with db:
        db.execute("delete from prog")
        db.executemany("insert into prog values (?,?,?,?,?,?,?,?,?)", rows)
        db.execute("insert or replace into meta values ('made', ?)", (str(time.time()),))
    db.close()
    return len(rows)


FIELDS = ("start", "stop", "title", "sub", "descr", "cats", "ep", "icon")


def _rows(cur):
    return [dict(zip(FIELDS, r)) for r in cur]


def now_next(db, key, t=None):
    t = t or time.time()
    return _rows(db.execute("select start,stop,title,sub,descr,cats,ep,icon from prog where ch=? and stop>? "
                            "order by start limit 2", (key, t)))


def window(db, keys, t0, t1):
    out = {k: [] for k in keys}
    for k in keys:
        out[k] = _rows(db.execute("select start,stop,title,sub,descr,cats,ep,icon from prog where ch=? and stop>? "
                                  "and start<? order by start", (k, t0, t1)))
    return out


def upcoming(db, title, key=None, t=None):
    """Future showings of a programme (by title), for "record every episode"."""
    t = t or time.time()
    q = "select ch,start,stop,title,sub,descr,cats,ep,icon from prog where lower(title)=lower(?) and start>?"
    args = [title, t - 60]
    if key:
        q += " and ch=?"
        args.append(key)
    return [dict(zip(("ch",) + FIELDS, r)) for r in db.execute(q + " order by start", args)]


def search(db, text, keys=None, t=None, limit=300):
    """Programmes from now on whose title (or episode title) matches a wildcard search."""
    rx = lineup.wildcard(text)
    if not rx:
        return []
    db.create_function("kmatch", 1, lambda s: 1 if s and rx.search(lineup.fold(s)) else 0, deterministic=True)
    t = t or time.time()
    rows = db.execute("select ch,start,stop,title,sub,descr,cats,ep,icon from prog where stop>? and "
                      "(kmatch(title) or kmatch(sub)) order by start limit ?", (t, limit * 3)).fetchall()
    out = [dict(zip(("ch",) + FIELDS, r)) for r in rows]
    if keys is not None:
        out = [p for p in out if p["ch"] in keys]
    return out[:limit]


def self_test():
    assert xmltv_time("20261118204100 +0000") == int(datetime.datetime(2026, 11, 18, 20, 41,
                                                                      tzinfo=datetime.timezone.utc).timestamp())
    assert xmltv_time("20261118204100 -0500") - xmltv_time("20261118204100 +0000") == 5 * 3600
    db = sqlite3.connect(":memory:")
    db.execute("create table prog (ch text, start int, stop int, title text, sub text, descr text, cats text, "
               "ep text, icon text)")
    now = int(time.time())
    db.executemany("insert into prog values (?,?,?,?,?,?,?,?,?)",
                   [("a", now - 100, now + 100, "Star Trek: Voyager", "", "", "", "", ""),
                    ("b", now + 100, now + 900, "Wheel of Fortune", "Star Week", "", "", "", ""),
                    ("c", now - 900, now - 100, "Star Trek", "", "", "", "", "")])
    assert [p["title"] for p in search(db, "star trek*")] == ["Star Trek: Voyager"]   # finished ones left out
    assert [p["title"] for p in search(db, "star")] == ["Star Trek: Voyager", "Wheel of Fortune"]
    assert search(db, "star", keys={"b"})[0]["ch"] == "b"
    print("guide self-test ok")


if __name__ == "__main__":
    self_test()
