"""KantanOS Watch TV: recordings (PVR).

The TV app writes what to record to schedule.json (one-off recordings and "every episode"
rules). The recorder service (kantanos-tv-recorder, running whenever someone is signed in)
reads it every few seconds, runs ffmpeg at the right times, keeps the PC awake while recording,
and writes what happened to status.json. Each file is written by one side only.
"""
import json
import os
import re
import signal
import subprocess
import sys
import time
import uuid

import lineup

SCHEDULE = os.path.join(lineup.DATA, "schedule.json")
STATUS = os.path.join(lineup.DATA, "status.json")
BEFORE, AFTER = 60, 180            # start a minute early, run three minutes over


def _load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def load_schedule():
    s = _load(SCHEDULE, {})
    s.setdefault("items", [])
    s.setdefault("rules", [])
    return s


def load_status():
    return _load(STATUS, {})


# ---- what the TV app calls -----------------------------------------------------------------
def add(channel, title, start, stop, sub=""):
    s = load_schedule()
    for it in s["items"]:
        if it["key"] == channel["key"] and abs(it["start"] - start) < 120 and not it.get("cancelled"):
            return it
    it = {"id": uuid.uuid4().hex[:12], "key": channel["key"], "channel": channel["name"],
          "number": channel.get("number"), "title": title or channel["name"], "sub": sub or "",
          "start": int(start), "stop": int(stop), "streams": channel["streams"]}
    s["items"].append(it)
    _save(SCHEDULE, s)
    return it


def cancel(item_id):
    s = load_schedule()
    for it in s["items"]:
        if it["id"] == item_id:
            it["cancelled"] = True
    _save(SCHEDULE, s)


def forget(item_id, delete_file=False):
    s = load_schedule()
    st = load_status().get(item_id, {})
    if delete_file:
        for f in st.get("files", []):
            try:
                os.remove(f)
            except OSError:
                pass
    s["items"] = [it for it in s["items"] if it["id"] != item_id]
    _save(SCHEDULE, s)


def add_rule(channel, title):
    s = load_schedule()
    if not any(r["title"].lower() == title.lower() and r.get("key") == channel["key"] for r in s["rules"]):
        s["rules"].append({"title": title, "key": channel["key"], "channel": channel["name"]})
        _save(SCHEDULE, s)


def remove_rule(title, key):
    s = load_schedule()
    s["rules"] = [r for r in s["rules"] if not (r["title"].lower() == title.lower() and r.get("key") == key)]
    _save(SCHEDULE, s)


def state_of(item, status=None, now=None):
    """scheduled | recording | done | failed | cancelled | missed"""
    now = now or time.time()
    st = (status or load_status()).get(item["id"], {})
    if item.get("cancelled") and not st.get("files"):
        return "cancelled"
    if st.get("state") in ("recording", "done", "failed"):
        return st["state"]
    if item["stop"] + AFTER < now:
        return "missed"
    return "scheduled"


def file_name(item, folder):
    when = time.strftime("%Y-%m-%d %H.%M", time.localtime(item["start"]))
    name = f"{item['title']} - {item['channel']} - {when}"
    name = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', " ", name).strip()[:150]
    return os.path.join(folder, name + ".ts")


# ---- the recorder service ------------------------------------------------------------------
class Service:
    def __init__(self):
        self.running = {}          # id -> (Popen, item)
        self.inhibit = None
        self.status = load_status()
        self.last_rules = 0

    def log(self, *a):
        print(*a, flush=True)

    def set_state(self, item_id, **kw):
        self.status.setdefault(item_id, {}).update(kw)
        _save(STATUS, self.status)

    def expand_rules(self, sched):
        """Adds upcoming showings of every "every episode" rule from the guide."""
        if not sched["rules"] or time.time() - self.last_rules < 600:
            return sched
        self.last_rules = time.time()
        try:
            import guide
            lu = lineup.load_saved()
            db = guide.connect()
        except Exception as e:                       # noqa: BLE001 - guide trouble mustn't stop recordings
            self.log("rules:", e)
            return sched
        chans = {c["key"]: c for c in (lu.channels if lu else [])}
        changed = False
        for r in sched["rules"]:
            for p in guide.upcoming(db, r["title"], r.get("key")):
                c = chans.get(p["ch"])
                if not c or p["start"] > time.time() + 2 * 86400:
                    continue
                if any(it["key"] == c["key"] and abs(it["start"] - p["start"]) < 120 for it in sched["items"]):
                    continue
                sched["items"].append({"id": uuid.uuid4().hex[:12], "key": c["key"], "channel": c["name"],
                                       "number": c.get("number"), "title": p["title"], "sub": p["sub"],
                                       "start": p["start"], "stop": p["stop"], "streams": c["streams"], "rule": True})
                changed = True
        db.close()
        if changed:
            _save(SCHEDULE, sched)
        return sched

    def start(self, it, folder):
        os.makedirs(folder, exist_ok=True)
        st = self.status.get(it["id"], {})
        files = st.get("files", [])
        tries = st.get("tries", 0)
        streams = it.get("streams") or []
        if not streams:
            self.set_state(it["id"], state="failed", why="no stream")
            return
        s = streams[tries % len(streams)]          # after a failure, try the backup stream
        out = file_name(it, folder)
        if files:                                  # restarted after a drop: a new part, nothing overwritten
            out = out[:-3] + f" (part {len(files) + 1}).ts"
        secs = max(30, int(it["stop"] + AFTER - time.time()))
        cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error", "-y",
               "-user_agent", s.get("ua") or "Mozilla/5.0 (X11; Linux x86_64) KantanOS-TV"]
        if s.get("ref"):
            cmd += ["-headers", f"Referer: {s['ref']}\r\n"]
        cmd += ["-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_on_network_error", "1",
                "-reconnect_delay_max", "10", "-i", s["url"], "-t", str(secs),
                "-map", "0:v:0?", "-map", "0:a?", "-c", "copy", "-f", "mpegts", out]
        p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, start_new_session=True)
        self.running[it["id"]] = (p, it)
        self.set_state(it["id"], state="recording", files=files + [out], tries=tries, started=time.time())
        self.log("recording", it["title"], "->", out)

    def check_running(self, sched):
        ids = {it["id"]: it for it in sched["items"]}
        for item_id, (p, it) in list(self.running.items()):
            now_it = ids.get(item_id)
            if now_it is None or now_it.get("cancelled"):       # stopped from the TV app
                p.send_signal(signal.SIGINT)
                try:
                    p.wait(10)
                except subprocess.TimeoutExpired:
                    p.kill()
                del self.running[item_id]
                self.set_state(item_id, state="done", stopped_early=True)
                continue
            if p.poll() is None:
                continue
            del self.running[item_id]
            err = p.stderr.read().decode(errors="replace")[-400:] if p.stderr else ""
            files = [f for f in self.status.get(item_id, {}).get("files", []) if os.path.exists(f)]
            got = sum(os.path.getsize(f) for f in files)
            if time.time() < it["stop"] - 30:           # ended early: the stream dropped
                tries = self.status.get(item_id, {}).get("tries", 0) + 1
                if tries < 20:
                    self.set_state(item_id, state="scheduled", tries=tries, files=files, why=err.strip()[-200:])
                    self.log("stream dropped, trying again:", it["title"], err.strip()[-120:])
                    continue
            self.set_state(item_id, state="done" if got > 200_000 else "failed", files=files,
                           why="" if got > 200_000 else (err.strip()[-200:] or "the channel sent nothing"))
        self.update_inhibit()

    def update_inhibit(self):
        """Keeps the PC from going to sleep while anything is being recorded."""
        if self.running and not self.inhibit:
            self.inhibit = subprocess.Popen(["systemd-inhibit", "--what=sleep:idle", "--who=KantanOS TV",
                                             "--why=Recording a TV programme", "--mode=block", "sleep", "infinity"],
                                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif not self.running and self.inhibit:
            self.inhibit.terminate()
            self.inhibit = None

    def tick(self):
        cfg = lineup.load_config()
        folder = cfg.get("record_dir") or lineup.DEFAULTS["record_dir"]
        sched = self.expand_rules(load_schedule())
        self.status = load_status()
        self.check_running(sched)
        now = time.time()
        for it in sched["items"]:
            if it.get("cancelled") or it["id"] in self.running:
                continue
            st = self.status.get(it["id"], {})
            if st.get("state") in ("done", "failed"):
                continue
            if it["start"] - BEFORE <= now < it["stop"] + AFTER - 30:
                self.start(it, folder)
        self.update_inhibit()

    def run(self):
        signal.signal(signal.SIGTERM, lambda *a: self.shutdown())
        self.log("KantanOS TV recorder ready")
        while True:
            try:
                self.tick()
            except Exception as e:                   # noqa: BLE001 - keep recording other things
                self.log("problem:", e)
            time.sleep(5)

    def shutdown(self):
        for item_id, (p, _it) in self.running.items():
            p.send_signal(signal.SIGINT)
            self.set_state(item_id, state="done", stopped_early=True)
        if self.inhibit:
            self.inhibit.terminate()
        sys.exit(0)


def self_test():
    it = {"title": "News: 6/7", "channel": "CBS", "start": 0}
    assert ":" not in os.path.basename(file_name(it, "/tmp")) and "/" not in os.path.basename(file_name(it, "/tmp"))
    assert state_of({"id": "x", "stop": 0}, {}, now=1000) == "missed"
    assert state_of({"id": "x", "stop": 5000}, {}, now=1000) == "scheduled"
    assert state_of({"id": "x", "stop": 5000, "cancelled": True}, {}, now=1000) == "cancelled"
    print("recorder self-test ok")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    else:
        Service().run()
