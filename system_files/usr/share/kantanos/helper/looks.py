"""Which outfit Kan-chan (or another character) wears right now.

A character pack can have looks/<name>/ folders (each with idle.png, blink.png, talk1.png, ...)
and a when.json listing which look to wear when; the first rule that fits wins and rules for
looks that aren't drawn yet are skipped:

  {"looks": [
    {"look": "doctor",  "context": "helper"},        while the Helper is fixing something
    {"look": "rain",    "weather": "rain"},          raining where the PC is
    {"look": "pyjamas", "hours": [22, 6]},           from 22:00 to 06:00
    {"look": "summer",  "months": [7, 8]},
    {"look": "hoodie",  "days": [5, 6]},             Saturday, Sunday (Monday = 0)
    {"choose": ["suit", "blazer"], "days": [0, 1, 2, 3, 4]}   one of these, a different one each day
    {"look": "everyday"}]}                           no conditions: the default
Weather can be "rain", "snow", "hot" (28 °C or more and dry) or "clear".

Weather comes from Open-Meteo for the town the KantanOS Weather widget shows (else the PC's
location from "ujust kantan-set-location"): only those coordinates are sent, the same request
the widget makes, at most every 30 minutes, and only when the pack has a weather look.
"""
import glob
import json
import os
import re
import time
import urllib.request

HOME = os.path.expanduser("~")
CACHE = os.path.join(os.environ.get("XDG_CACHE_HOME", os.path.join(HOME, ".cache")), "kantanos", "weather-now.json")
RAIN = set(range(51, 68)) | set(range(80, 83)) | set(range(95, 100))
SNOW = set(range(71, 78)) | {85, 86}
HOT = 28          # °C: swimwear weather


def where():
    """(latitude, longitude) of the weather widget's town, else the PC's set location."""
    for f in (os.path.join(HOME, ".config", "plasma-org.kde.plasma.desktop-appletsrc"),):
        try:
            text = open(f, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        la, lo = re.search(r"^latitude=([-\d.]+)", text, re.M), re.search(r"^longitude=([-\d.]+)", text, re.M)
        if la and lo and not (float(la.group(1)) == 0 and float(lo.group(1)) == 0):
            return float(la.group(1)), float(lo.group(1))
    try:
        lines = [l.strip() for l in open("/etc/geolocation") if l.strip() and not l.startswith("#")]
        return float(lines[0]), float(lines[1])
    except (OSError, ValueError, IndexError):
        return None


def weather_now(max_age=1800, fetch=True):
    """'rain', 'snow', 'clear' (anything else) or '' when unknown."""
    try:
        c = json.load(open(CACHE))
        if time.time() - c["time"] < max_age:
            return c["weather"]
    except (OSError, ValueError, KeyError):
        pass
    place = where() if fetch else None
    if not place:
        return ""
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={place[0]:.2f}&longitude={place[1]:.2f}"
           "&current=weather_code,temperature_2m")
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            now = json.load(r)["current"]
            code, temp = int(now["weather_code"]), float(now.get("temperature_2m", 0))
    except (OSError, ValueError, KeyError, TypeError):
        return ""
    w = "rain" if code in RAIN else "snow" if code in SNOW else "hot" if temp >= HOT else "clear"
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    with open(CACHE + ".tmp", "w") as f:
        json.dump({"time": time.time(), "weather": w, "code": code}, f)
    os.replace(CACHE + ".tmp", CACHE)
    return w


def rules(pack):
    try:
        with open(os.path.join(pack, "when.json"), encoding="utf-8") as f:
            return json.load(f).get("looks", [])
    except (OSError, ValueError):
        return []


def drawn(pack, look):
    return os.path.isfile(os.path.join(pack, "looks", look, "idle.png"))


def fits(rule, now, weather, context):
    if "context" in rule and rule["context"] != context:
        return False
    if "weather" in rule and rule["weather"] != weather():
        return False
    if "hours" in rule:
        a, b = rule["hours"]
        h = now.tm_hour
        if not (a <= h < b if a < b else h >= a or h < b):
            return False
    if "months" in rule and now.tm_mon not in rule["months"]:
        return False
    if "days" in rule and now.tm_wday not in rule["days"]:
        return False
    return True


def current(pack, context="", now=None, weather=None):
    """The folder of the look to wear now (the pack itself when it has no looks)."""
    if not pack or not os.path.isdir(os.path.join(pack, "looks")):
        return pack
    now = now or time.localtime()
    cached = {}

    def w():
        if "w" not in cached:
            cached["w"] = weather if weather is not None else weather_now()
        return cached["w"]
    for rule in rules(pack):
        if "choose" in rule:            # one of several, a different one each day (same all day)
            pool = [l for l in rule["choose"] if drawn(pack, l)]
            if pool and fits(rule, now, w, context):
                day = time.mktime(now[:3] + (12, 0, 0, 0, 0, -1)) // 86400
                return os.path.join(pack, "looks", pool[int(day) % len(pool)])
            continue
        look = rule.get("look", "")
        if drawn(pack, look) and fits(rule, now, w, context):
            return os.path.join(pack, "looks", look)
    first = sorted(glob.glob(os.path.join(pack, "looks", "*", "idle.png")))
    return os.path.dirname(first[0]) if first else pack


def self_test():
    import tempfile
    tmp = tempfile.mkdtemp()
    for look in ("everyday", "rain", "pyjamas"):
        os.makedirs(os.path.join(tmp, "looks", look))
        open(os.path.join(tmp, "looks", look, "idle.png"), "w").close()
    json.dump({"looks": [{"look": "doctor", "context": "helper"}, {"look": "rain", "weather": "rain"},
                         {"look": "pyjamas", "hours": [22, 6]}, {"look": "summer", "months": [7, 8]},
                         {"look": "everyday"}]}, open(os.path.join(tmp, "when.json"), "w"))
    t = lambda h, mon=11: time.struct_time((2026, mon, 19, h, 0, 0, 3, 323, 0))  # noqa: E731
    name = lambda **k: os.path.basename(current(tmp, **k))                       # noqa: E731
    assert name(now=t(14), weather="clear") == "everyday"
    assert name(now=t(14), weather="rain") == "rain"
    assert name(now=t(23), weather="clear") == "pyjamas" and name(now=t(5), weather="") == "pyjamas"
    assert name(now=t(14, 8), weather="clear") == "everyday"            # no summer drawing yet
    assert name(now=t(14), weather="clear", context="helper") == "everyday"   # no doctor drawing yet
    assert current(os.path.join(tmp, "looks", "rain")) == os.path.join(tmp, "looks", "rain")  # no looks: itself
    for look in ("suit", "blazer"):
        os.makedirs(os.path.join(tmp, "looks", look))
        open(os.path.join(tmp, "looks", look, "idle.png"), "w").close()
    json.dump({"looks": [{"choose": ["suit", "blazer", "undrawn"], "days": [0, 1, 2, 3, 4]}, {"look": "everyday"}]},
              open(os.path.join(tmp, "when.json"), "w"))
    day = lambda d: time.localtime(time.mktime((2026, 11, d, 14, 0, 0, 0, 0, -1)))       # noqa: E731
    picks = {name(now=day(d), weather="clear") for d in (16, 17, 18)}                   # Mon-Wed
    assert picks == {"suit", "blazer"}, picks
    assert name(now=day(16), weather="clear") == name(now=day(16), weather="clear")     # same all day
    assert name(now=day(21), weather="clear") == "everyday"                             # Saturday
    return True


if __name__ == "__main__":
    import sys
    if sys.argv[1:2] == ["--self-test"]:
        print("ok" if self_test() else "fail")
    elif sys.argv[1:2] == ["--dir"]:               # for the desktop buddy: the folder, then its files
        d = current(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
        print(d)
        print("\n".join(sorted(os.listdir(d))) if d and os.path.isdir(d) else "")
