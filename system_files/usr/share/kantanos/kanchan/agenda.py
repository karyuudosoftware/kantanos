"""Kan-chan's view of the person's calendar, for reminders and "what's on today?".

The appointments stay in the person's own accounts (Outlook, Google, iCloud, ...). Each account
can give a private calendar link (an .ics address): Kan-chan reads it, read-only, and keeps a
copy on this PC so reminders still work when the internet is down. The links are kept in the
person's own settings file (only they can read it), never in KantanOS itself.

(Named agenda, not calendar, so it doesn't hide Python's own calendar module.)
"""
import datetime
import hashlib
import json
import os
import re
import time
import urllib.request

HOME = os.path.expanduser("~")
CACHE = os.path.join(os.environ.get("XDG_CACHE_HOME", os.path.join(HOME, ".cache")), "kantanos", "calendar")
STATE = os.path.join(os.environ.get("XDG_STATE_HOME", os.path.join(HOME, ".local", "state")), "kantanos", "reminders.json")
REFRESH = 15 * 60
BEFORE = (60, 15)                 # minutes before an appointment that she reminds
MORNING = 7                       # the day's summary comes at the first check after 7 am
AGENT = {"User-Agent": "KantanOS-Kanchan/1.0 (calendar reminders)"}


def clean_link(url):
    """Calendar links as people paste them: webcal:// becomes https://. Only https is accepted."""
    url = (url or "").strip()
    if url.lower().startswith("webcal://"):
        url = "https://" + url[9:]
    if os.environ.get("KANTAN_TEST_CALENDAR_HTTP") and url.startswith("http://10.0.2.2:"):
        return url                      # testing in the VM with a calendar served from the build PC
    return url if re.match(r"(?i)^https://[^\s/]+/\S+$", url) else ""


def _cache_path(url):
    return os.path.join(CACHE, hashlib.sha256(url.encode()).hexdigest()[:20] + ".ics")


def fetch(url, force=False):
    """The calendar's text: a fresh copy every 15 minutes, else the copy kept on this PC."""
    path = _cache_path(url)
    try:
        fresh = time.time() - os.path.getmtime(path) < REFRESH
    except OSError:
        fresh = False
    if fresh and not force:
        return open(path, encoding="utf-8", errors="replace").read()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=AGENT), timeout=30) as r:
            data = r.read(20_000_000).decode("utf-8", errors="replace")
        if "BEGIN:VCALENDAR" not in data:
            raise ValueError("that link isn't a calendar")
        os.makedirs(CACHE, exist_ok=True)
        fd = os.open(path + ".tmp", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
        os.replace(path + ".tmp", path)
        return data
    except (OSError, ValueError):
        if os.path.exists(path):
            return open(path, encoding="utf-8", errors="replace").read()
        raise


def _local(dt):
    """datetime or date → (aware local datetime, all_day)."""
    if not isinstance(dt, datetime.datetime):
        return datetime.datetime.combine(dt, datetime.time()).astimezone(), True
    if dt.tzinfo is None:
        return dt.astimezone(), False                  # "floating" times are this PC's time
    return dt.astimezone(), False


def events(text, start, end):
    """Appointments that start between start and end (aware datetimes), repeats expanded:
    [{"title", "start", "end", "all_day", "where", "uid"}] sorted by start."""
    import icalendar
    from dateutil import rrule
    cal = icalendar.Calendar.from_ical(text)
    found, moved = [], {}
    items = [c for c in cal.walk("VEVENT")]
    for c in items:                                    # single changed occurrences of a repeat
        if c.get("RECURRENCE-ID"):
            rid = c.decoded("RECURRENCE-ID")
            moved.setdefault(str(c.get("UID")), set()).add(_local(rid)[0])
    for c in items:
        if str(c.get("STATUS", "")).upper() == "CANCELLED":
            continue
        try:
            s = c.decoded("DTSTART")
        except KeyError:
            continue
        s_local, all_day = _local(s)
        if c.get("DTEND"):
            length = _local(c.decoded("DTEND"))[0] - s_local
        elif c.get("DURATION"):
            length = c.decoded("DURATION")
        else:
            length = datetime.timedelta(days=1) if all_day else datetime.timedelta(0)
        uid = str(c.get("UID", ""))
        title = str(c.get("SUMMARY", "")).strip() or "an appointment"
        where = str(c.get("LOCATION", "")).strip()
        starts = []
        if c.get("RRULE") and not c.get("RECURRENCE-ID"):
            try:
                rule_text = c.get("RRULE").to_ical().decode()
                base = s if isinstance(s, datetime.datetime) else datetime.datetime.combine(s, datetime.time())
                if isinstance(base, datetime.datetime) and base.tzinfo is None and not all_day:
                    base = base.astimezone()
                if all_day:
                    rule_text = re.sub(r"UNTIL=(\d{8})T?\d*Z?", r"UNTIL=\1T235959", rule_text)
                elif base.tzinfo is not None:
                    rule_text = re.sub(r"UNTIL=(\d{8})(;|$)", r"UNTIL=\1T235959Z\2", rule_text)
                rs = rrule.rruleset()
                rs.rrule(rrule.rrulestr(rule_text, dtstart=base, ignoretz=False))
                exd = c.get("EXDATE")
                for ex in (exd if isinstance(exd, list) else [exd] if exd else []):
                    for d in ex.dts:
                        rs.exdate(_to_base(d.dt, base))
                lo = _to_base(start - length - datetime.timedelta(days=1), base)
                hi = _to_base(end, base)
                for occ in rs.between(lo, hi, inc=True):
                    starts.append(_local(occ.date() if all_day else occ)[0])
            except (ValueError, TypeError, AttributeError):
                starts = [s_local]
        else:
            starts = [s_local]
        skip = moved.get(uid, set()) if not c.get("RECURRENCE-ID") else set()
        for st in starts:
            if st in skip:
                continue
            if start <= st < end or (all_day and st <= start < st + length):
                found.append({"title": title, "start": st, "end": st + length, "all_day": all_day,
                              "where": where, "uid": uid})
    found.sort(key=lambda e: (not e["all_day"], e["start"]))
    return found


def _to_base(dt, base):
    """Makes dt comparable with the rule's start (aware or not)."""
    if not isinstance(dt, datetime.datetime):
        dt = datetime.datetime.combine(dt, datetime.time())
    if base.tzinfo is None:
        return dt.astimezone().replace(tzinfo=None) if dt.tzinfo else dt
    return dt.astimezone(base.tzinfo) if dt.tzinfo else dt.replace(tzinfo=base.tzinfo)


def all_events(links, start, end, force=False):
    """From every calendar link; a link that can't be read is skipped (errors listed)."""
    out, errors = [], []
    for link in links:
        url = clean_link(link.get("url") if isinstance(link, dict) else link)
        if not url:
            continue
        try:
            out += events(fetch(url, force), start, end)
        except Exception as e:  # noqa: BLE001 - one bad calendar mustn't stop the others
            errors.append(str(e)[:120])
    seen, uniq = set(), []
    for e in sorted(out, key=lambda e: (not e["all_day"], e["start"])):
        key = (e["title"].lower(), e["start"])
        if key not in seen:
            seen.add(key)
            uniq.append(e)
    return uniq, errors


def clock(dt):
    return dt.strftime("%I:%M %p").lstrip("0").replace(":00 ", " ").lower()


def describe(e, with_time=True):
    where = f" at {e['where']}" if e.get("where") and len(e["where"]) < 80 else ""
    if e["all_day"] or not with_time:
        return f"{e['title']}{where}"
    return f"{e['title']} at {clock(e['start'])}{where}"


def join(parts):
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]


def day_text(evs, day_word="today"):
    if not evs:
        return f"There's nothing in your calendar for {day_word}."
    return f"For {day_word} you have {join([describe(e) for e in evs])}."


def day_range(day):
    s = datetime.datetime.combine(day, datetime.time()).astimezone()
    return s, s + datetime.timedelta(days=1)


def ask_day(text, now=None):
    """Which day "what's on today/tomorrow/on Friday" means, or None if it isn't about the calendar."""
    t = (text or "").lower()
    if not re.search(r"\b(what'?s on|what is on|appointments?|agenda|calendar|diary|schedule|plans? for|"
                     r"am i (doing|busy|free)|have i got (anything|something)|do i have (anything|something))\b", t):
        return None
    now = now or datetime.datetime.now()
    if "tomorrow" in t:
        return now.date() + datetime.timedelta(days=1), "tomorrow"
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for i, d in enumerate(days):
        if d in t:
            ahead = (i - now.weekday()) % 7 or 7
            day = now.date() + datetime.timedelta(days=ahead)
            return day, f"{d.title()} {day.day} {day.strftime('%B')}"
    return now.date(), "today"


# ---- reminders (run every 5 minutes by kanchan-remind) --------------------------------------
def load_state():
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_state(st):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f)
    os.replace(tmp, STATE)


def due(evs, st, now=None):
    """The reminders to give now: [text]; st (the state) is updated so each is given once."""
    now = now or datetime.datetime.now().astimezone()
    out = []
    today = now.date().isoformat()
    todays = [e for e in evs if e["start"].date() == now.date() or (e["all_day"] and e["start"] <= now < e["end"])]
    if now.hour >= MORNING and st.get("morning") != today:
        st["morning"] = today
        if todays:
            out.append("Good morning! " + day_text(todays))
    done = set(st.get("done", []))
    for e in evs:
        if e["all_day"] or e["start"] <= now:
            continue
        left = (e["start"] - now).total_seconds() / 60
        keys = [f"{e['uid']}|{e['start'].isoformat()}|{m}" for m in BEFORE]
        fire = [m for m, k in zip(BEFORE, keys) if left <= m and k not in done]
        if not fire:
            continue
        for k in keys:                      # a late start gives only the nearest reminder
            if int(k.rsplit("|", 1)[1]) >= min(fire):
                done.add(k)
        mins = round(left)
        soon = ("in about an hour" if mins > 45 else f"in {mins} minutes" if mins > 1 else "now")
        out.append(f"Reminder: {describe(e)}, {soon}.")
    cutoff = (now - datetime.timedelta(days=2)).isoformat()
    st["done"] = sorted(k for k in done if k.split("|")[1] >= cutoff)
    return out


SAMPLE = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:a1
SUMMARY:Dentist
LOCATION:Smile Dental
DTSTART:{d}T100000
DTEND:{d}T103000
END:VEVENT
BEGIN:VEVENT
UID:a2
SUMMARY:Bin day
DTSTART;VALUE=DATE:{d}
DTEND;VALUE=DATE:{n}
END:VEVENT
BEGIN:VEVENT
UID:a3
SUMMARY:Choir
DTSTART:{w}T190000
DTEND:{w}T200000
RRULE:FREQ=WEEKLY;COUNT=10
EXDATE:{x}T190000
END:VEVENT
END:VCALENDAR
"""


def self_test():
    day = datetime.date.today()
    fmt = lambda d: d.strftime("%Y%m%d")   # noqa: E731
    text = SAMPLE.format(d=fmt(day), n=fmt(day + datetime.timedelta(days=1)),
                         w=fmt(day - datetime.timedelta(days=7)), x=fmt(day + datetime.timedelta(days=7)))
    s, e = day_range(day)
    evs = events(text, s, e)
    titles = [x["title"] for x in evs]
    assert titles == ["Bin day", "Dentist", "Choir"], titles
    s2, e2 = day_range(day + datetime.timedelta(days=7))
    assert [x["title"] for x in events(text, s2, e2)] == [], "the skipped week"
    assert "Dentist at 10 am at Smile Dental" in day_text(evs)
    st = {}
    at = evs[1]["start"] - datetime.timedelta(minutes=50)
    msgs = due(evs, st, at)
    assert any("Dentist" in m and "about an hour" in m for m in msgs), msgs
    assert not [m for m in due(evs, st, at + datetime.timedelta(minutes=2)) if "Dentist" in m]
    assert any("in 10 minutes" in m for m in due(evs, st, at + datetime.timedelta(minutes=40)))
    assert ask_day("what's on tomorrow?")[1] == "tomorrow" and ask_day("tell me a joke") is None
    assert clean_link("webcal://outlook.live.com/owa/calendar/x/reachcalendar.ics").startswith("https://")
    assert clean_link("file:///etc/passwd") == ""
    print("agenda self-test ok")


if __name__ == "__main__":
    self_test()
