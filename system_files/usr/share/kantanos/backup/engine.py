"""KantanOS Backups: the part without a window (used by the window and the half-hourly timer).

Backups are made with restic: each one only stores what changed, every one can be opened
like a folder, and everything is locked with the family's backup key before it leaves the PC
(Google Drive and OneDrive only ever see scrambled data). Where they go:
  usb      a USB drive (by its filesystem id, mounted when it's plugged in)
  nas      a NAS share connected with "Connect your NAS" (/var/mnt/nas/<share>)
  gdrive   Google Drive, through rclone (the person signs in to Google in their browser)
  onedrive OneDrive, the same way

  ~/.config/kantanos/backup.json    where, which folders
  ~/.config/kantanos/backup.key     the backup key (only this user can read it)
  ~/.local/state/kantanos/backup.json   how the last backups went
"""
import datetime
import fcntl
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import time

HOME = os.path.expanduser("~")
CONF_DIR = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.join(HOME, ".config")), "kantanos")
CONF = os.path.join(CONF_DIR, "backup.json")
KEY = os.path.join(CONF_DIR, "backup.key")
STATE_DIR = os.path.join(os.environ.get("XDG_STATE_HOME", os.path.join(HOME, ".local", "state")), "kantanos")
STATE = os.path.join(STATE_DIR, "backup.json")
BROWSE = os.path.join(HOME, ".cache", "kantanos", "backups")
NAS_ROOT = os.environ.get("KANTAN_NAS_ROOT", "/var/mnt/nas")
FOLDER = "KantanOS Backup"
HOST = socket.gethostname()
TIMER = "kantanos-backup.timer"
SERVICE = "kantanos-backup.service"
CLOUD = {"gdrive": ("kantan-gdrive", "drive", ["scope=drive.file"], "Google Drive"),
         "onedrive": ("kantan-onedrive", "onedrive", [], "OneDrive")}
FREE_CLOUD_GB = {"gdrive": 15, "onedrive": 5}

# (folder in the home folder, name shown, ticked at first)
FOLDERS = [("Desktop", "Desktop", True), ("Documents", "Documents", True), ("Pictures", "Pictures", True),
           ("Music", "Music", True), ("Videos", "Videos", True), ("Downloads", "Downloads", False),
           (".local/share/kantanos", "Kan-chan's memories and KantanOS settings", True)]
EXTRA_WITH_SETTINGS = [".config/kantanos"]           # backed up with "KantanOS settings" (never the key)
EXCLUDE = ["*.tmp", "*.part", "*.crdownload", ".cache", ".Trash-*", "backup.key"]
KEEP = ["--keep-last", "48", "--keep-daily", "30", "--keep-weekly", "12", "--keep-monthly", "24"]
KEY_LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"     # no 0/O or 1/I to mix up when writing it down


# ---- settings and state --------------------------------------------------------------------
def _read(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            v = json.load(f)
        return v if isinstance(v, dict) else default
    except (OSError, ValueError):
        return default


def _write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".new"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def config():
    return _read(CONF, {})


def save_config(cfg):
    _write(CONF, cfg)


def state():
    return _read(STATE, {})


def save_state(**changes):
    st = state()
    st.update(changes)
    _write(STATE, st)
    return st


def new_key():
    return "-".join("".join(secrets.choice(KEY_LETTERS) for _ in range(5)) for _ in range(6))


def clean_key(text):
    """What they typed, the way the key is stored (spaces and case don't matter)."""
    t = re.sub(r"[^A-Za-z0-9]", "", text or "").upper()
    return "-".join(t[i:i + 5] for i in range(0, len(t), 5)) if len(t) == 30 else (text or "").strip()


def save_key(key):
    os.makedirs(CONF_DIR, exist_ok=True)
    fd = os.open(KEY + ".new", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(key + "\n")
    os.replace(KEY + ".new", KEY)


# ---- places --------------------------------------------------------------------------------
def _run(cmd, timeout=30, env=None, input=None):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env, input=input)
    except (OSError, subprocess.TimeoutExpired) as e:
        return subprocess.CompletedProcess(cmd, 1, "", str(e))


def usb_drives():
    """Plugged-in USB drives with a filesystem: [{uuid, label, size, mount}]."""
    out = _run(["lsblk", "-J", "-b", "-o", "NAME,PATH,UUID,LABEL,MOUNTPOINT,RM,HOTPLUG,TRAN,FSTYPE,SIZE"]).stdout
    try:
        devs = json.loads(out).get("blockdevices", [])
    except ValueError:
        return []
    found = []

    def walk(d, removable):
        removable = removable or d.get("rm") in (True, "1") or d.get("hotplug") in (True, "1") or d.get("tran") == "usb"
        if removable and d.get("uuid") and d.get("fstype") not in (None, "swap", "crypto_LUKS", "LVM2_member", "iso9660"):
            found.append({"uuid": d["uuid"], "label": d.get("label") or "", "size": int(d.get("size") or 0),
                          "mount": d.get("mountpoint") or ""})
        for c in d.get("children") or []:
            walk(c, removable)
    for d in devs:
        walk(d, False)
    return found


def nas_shares():
    try:
        return sorted(n for n in os.listdir(NAS_ROOT) if os.path.isdir(os.path.join(NAS_ROOT, n)))
    except OSError:
        return []


def mount_usb(uuid):
    """Where the drive is mounted (mounting it if it's plugged in), or "" when it isn't here."""
    m = _run(["findmnt", "-n", "-o", "TARGET", "--source", f"UUID={uuid}"]).stdout.strip().splitlines()
    if m:
        return m[0]
    dev = f"/dev/disk/by-uuid/{uuid}"
    if not os.path.exists(dev):
        return ""
    _run(["udisksctl", "mount", "-b", dev, "--no-user-interaction"], timeout=60)
    m = _run(["findmnt", "-n", "-o", "TARGET", "--source", f"UUID={uuid}"]).stdout.strip().splitlines()
    return m[0] if m else ""


def place_name(cfg):
    where = cfg.get("where")
    if where == "usb":
        return f"the USB drive “{cfg.get('label') or 'backup drive'}”"
    if where == "nas":
        return f"the NAS (“{cfg.get('share')}”)"
    if where in CLOUD:
        return CLOUD[where][3]
    return "nowhere yet"


def repo(cfg, mount=True):
    """The restic repository for these settings, or "" when it can't be reached right now."""
    where = cfg.get("where")
    if where == "usb":
        m = mount_usb(cfg.get("uuid", "")) if mount else ""
        return os.path.join(m, FOLDER, HOST) if m else ""
    if where == "nas":
        base = os.path.join(NAS_ROOT, cfg.get("share", ""))
        return os.path.join(base, FOLDER, HOST) if cfg.get("share") and os.path.isdir(base) else ""
    if where in CLOUD:
        return f"rclone:{CLOUD[where][0]}:{FOLDER}/{HOST}"
    return ""


def cloud_ready(where):
    return CLOUD[where][0] + ":" in _run(["rclone", "listremotes"]).stdout.split()


def connect_cloud(where):
    """Signs in to Google Drive or OneDrive: rclone opens the browser, the person signs in there.
    Returns "" when it worked, else what went wrong."""
    name, kind, extra, _label = CLOUD[where]
    if cloud_ready(where):
        return ""
    r = _run(["rclone", "config", "create", name, kind, *extra], timeout=600)
    return "" if r.returncode == 0 and cloud_ready(where) else (r.stderr.strip().splitlines() or ["sign-in didn't finish"])[-1]


# ---- restic --------------------------------------------------------------------------------
def restic(args, repository, key=None, timeout=None, json_out=False):
    """Runs restic with the saved key file, or with `key` (a key being typed in or just made)."""
    env = dict(os.environ, RESTIC_REPOSITORY=repository, RESTIC_PROGRESS_FPS="0.2")
    for k in ("RESTIC_PASSWORD", "RESTIC_PASSWORD_FILE", "RESTIC_PASSWORD_COMMAND"):
        env.pop(k, None)
    if key is None:
        env["RESTIC_PASSWORD_FILE"] = KEY
    else:
        env["RESTIC_PASSWORD"] = key
    return _run(["restic", *args, *(["--json"] if json_out else [])], timeout=timeout, env=env)


def repo_exists(repository):
    """True when this place already has a backup (so it needs its own key, not a new one)."""
    if not repository.startswith("rclone:"):
        return os.path.exists(os.path.join(repository, "config"))
    r = restic(["cat", "config"], repository, key="x", timeout=120)
    return "wrong password" in (r.stderr or "").lower() or r.returncode == 0


def check_key(repository, key):
    r = restic(["cat", "config"], repository, key=key, timeout=120)
    return r.returncode == 0


def create(repository, key):
    if not repository.startswith("rclone:"):
        os.makedirs(repository, exist_ok=True)
    r = restic(["init"], repository, key=key, timeout=300)
    return "" if r.returncode == 0 else (r.stderr.strip().splitlines() or ["couldn't create it"])[-1]


def paths(cfg):
    out = []
    for rel in cfg.get("folders", []):
        p = os.path.join(HOME, rel)
        if os.path.exists(p):
            out.append(p)
        if rel == ".local/share/kantanos":
            out += [os.path.join(HOME, e) for e in EXTRA_WITH_SETTINGS if os.path.exists(os.path.join(HOME, e))]
    return out


def folder_size(rel):
    r = _run(["du", "-sb", os.path.join(HOME, rel)], timeout=120)
    try:
        return int(r.stdout.split()[0])
    except (IndexError, ValueError):
        return 0


def snapshots(cfg):
    rp = repo(cfg)
    if not rp:
        return None
    r = restic(["snapshots", "--host", HOST], rp, timeout=300, json_out=True)
    try:
        snaps = json.loads(r.stdout or "[]") or []
    except ValueError:
        return None
    return sorted(snaps, key=lambda s: s.get("time", ""), reverse=True)


# ---- the half-hourly backup ----------------------------------------------------------------
def notify(title, body, once_per_day_key=None):
    if once_per_day_key:
        st = state()
        if time.time() - st.get(once_per_day_key, 0) < 20 * 3600:
            return
        save_state(**{once_per_day_key: time.time()})
    _run(["notify-send", "-a", "Backups", "-i", "drive-harddisk", title, body], timeout=10)


def run(force=False):
    """One backup now (the timer calls this every 30 minutes). Returns a short result."""
    cfg = config()
    if not cfg.get("where") or not os.path.exists(KEY) or (cfg.get("paused") and not force):
        return "not set up"
    os.makedirs(STATE_DIR, exist_ok=True)
    lock = open(os.path.join(STATE_DIR, "backup.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return "already running"
    now = time.time()
    save_state(last_try=now, running=True)
    try:
        rp = repo(cfg)
        if not rp:
            st = save_state(waiting=place_name(cfg), running=False)
            if now - st.get("last_ok", now) > 3 * 86400:
                notify("Your files haven't been backed up for a while",
                       f"Plug in or switch on {place_name(cfg)} and the backup will happen by itself.", "nag_missing")
            return "waiting"
        src = paths(cfg)
        if not src:
            save_state(running=False, error="none of the chosen folders exist")
            return "nothing to back up"
        args = ["backup", "--host", HOST, "--tag", "kantanos", "--exclude-caches", "--one-file-system"]
        for e in EXCLUDE:
            args += ["--exclude", e]
        r = restic(args + src, rp, json_out=True)
        summary = {}
        for line in (r.stdout or "").splitlines():
            if '"message_type":"summary"' in line.replace(" ", ""):
                try:
                    summary = json.loads(line)
                except ValueError:
                    pass
        if r.returncode not in (0, 3) or not summary:          # 3 = some files couldn't be read
            err = (r.stderr or "").strip().splitlines()
            save_state(running=False, error=err[-1] if err else "the backup didn't finish", waiting="")
            notify("A backup didn't work", "Open Backups to see what happened.", "nag_error")
            return "error"
        st = save_state(running=False, last_ok=now, error="", waiting="", place=place_name(cfg),
                        added=summary.get("data_added", 0), files=summary.get("total_files_processed", 0),
                        unreadable=r.returncode == 3)
        if now - st.get("last_tidy", 0) > 86400:               # once a day: drop old versions
            t = restic(["forget", "--host", HOST, "--prune", *KEEP], rp, timeout=3 * 3600)
            if t.returncode == 0:
                save_state(last_tidy=now)
        return "ok"
    finally:
        if state().get("running"):
            save_state(running=False)
        lock.close()


def when_text(stamp, now=None):
    if not stamp:
        return "never"
    now = now or time.time()
    mins = int((now - stamp) // 60)
    if mins < 1:
        return "just now"
    if mins < 60:
        return f"{mins} minute{'s' if mins != 1 else ''} ago"
    d = datetime.datetime.fromtimestamp(stamp)
    today = datetime.date.fromtimestamp(now)
    if d.date() == today:
        return f"today at {d:%H:%M}"
    if d.date() == today - datetime.timedelta(days=1):
        return f"yesterday at {d:%H:%M}"
    return f"{d:%A %-d %B} at {d:%H:%M}"


def size_text(n):
    for unit in ("bytes", "KB", "MB", "GB", "TB"):
        if n < 1000 or unit == "TB":
            return f"{n:.0f} {unit}" if unit in ("bytes", "KB") else f"{n:.1f} {unit}"
        n /= 1000


def timer(on):
    if shutil.which("systemctl"):
        _run(["systemctl", "--user", "enable" if on else "disable", "--now", TIMER])


if __name__ == "__main__":
    import sys
    print(run(force="--now" in sys.argv))
