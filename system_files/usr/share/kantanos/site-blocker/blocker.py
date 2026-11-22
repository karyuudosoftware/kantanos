"""KantanOS site blocker: what both the window and the root helper use.

Bad sites are blocked in two ways, each with its own switch:

1. A list of site names kept by Dan Pollock (https://someonewhocares.org/hosts/, free for
   non-commercial use with this credit). The PC fetches it itself once a week and writes the
   names into its own marked part of /etc/hosts, so every browser and app refuses them.
   The list's sections are sorted into five plain categories that can be turned off one by
   one, and any site can be put on an "always allow" list.
2. A safe look-up service (Quad9): systemd-resolved asks Quad9, which refuses names known
   for viruses and scams, including ones too new for any list.

Only site NAMES are ever taken from the download, and every blocking line is written here
(always "0.0.0.0 name"), so a tampered list can't send a real site somewhere else. Names
KantanOS itself needs (updates, apps) are never blocked, whatever the list says.

  python3 blocker.py --self-test
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request

LIST_URL = "https://someonewhocares.org/hosts/zero/hosts"
LIST_HOST = "someonewhocares.org"
CREDIT = "The list is kept by Dan Pollock: someonewhocares.org/hosts (free for non-commercial use)."
BEGIN = "# >>> KantanOS site blocker: this part is rewritten automatically (Block bad sites) >>>"
END = "# <<< KantanOS site blocker <<<"
MAX_BYTES = 8 * 1024 * 1024
MIN_NAMES = 3000                 # a real list has over 13,000; fewer means a broken download
STALE = 6.5 * 86400              # fetch again after about a week

# (id, title, what it is, in plain words)
CATEGORIES = [
    ("harm", "Viruses, scams and fake sites",
     "Sites known for spreading viruses, stealing passwords or tricking people. Best left on."),
    ("shock", "Shock sites",
     "Sites made to upset or disgust whoever opens them. Best left on."),
    ("spy", "Tracking and spying",
     "Hidden counters that follow what you do from one site to the next."),
    ("ads", "Adverts and spam",
     "The companies that put adverts on other sites. Pages load faster without them; a few sites "
     "leave gaps or ask you to allow adverts."),
    ("shop", "Shop and deal links",
     "Sponsored results in a search, and the links in deal emails and price comparison sites, pass "
     "through these on the way to the shop. Turn this off if a shop link won't open."),
]
TITLES = {c[0]: c[1] for c in CATEGORIES}

# The list's own sections → our categories. A section we don't know yet counts as "harm":
# better blocked under the switch people leave on.
SECTIONS = {
    "hijack-sites": "harm", "malware-sites": "harm", "pegasus-spyware-sites": "harm",
    "popup-traps": "harm", "ecard-scam-sites": "harm",
    "shock-sites": "shock",
    "spyware-sites": "spy", "maybe-spy": "spy", "red-sheriff-sites": "spy", "cydoor-sites": "spy",
    "2o7-sites": "spy", "oewabox-sites": "spy", "canvass-fingerprinting-sites": "spy",
    "evercookies-sites": "spy", "hitbox-sites": "spy", "extreme-dm-sites": "spy", "IVW-sites": "spy",
    "Windows10": "spy",
    "ad-sites": "ads", "maybe-ads": "ads", "doubleclick-sites": "ads", "intellitxt-sites": "ads",
    "yahoo-ad-sites": "ads", "realmedia-sites": "ads", "fastclick-sites": "ads",
    "belo-interactive-sites": "ads", "wiki-spam-sites": "ads",
}
SKIP_SECTIONS = {"localhost", "shortcut-examples"}

# Click-through services that shop links pass through. Names on the list (in the advert or
# tracking sections) that belong to these get the "shop" switch of their own.
SHOP_SUFFIXES = (
    "googleadservices.com", "dartsearch.net", "linksynergy.com", "shareasale.com", "anrdoezrs.net",
    "dpbolvw.net", "jdoqocy.com", "kqzyfj.com", "tkqlhce.com", "lduhtrp.net", "ftjcfx.com", "tqlkg.com",
    "awltovhc.com", "yceml.net", "afcyhf.com", "apmebf.com", "emjcd.com", "skimresources.com",
    "redirectingat.com", "viglink.com", "tradedoubler.com", "zanox.com", "awin1.com", "webgains.com",
    "effiliation.com", "pjtra.com", "pjatr.com", "pntra.com", "pntrac.com", "pntrs.com", "gopjn.com",
    "pxf.io", "sjv.io", "ojrq.net", "prf.hn", "avantlink.com", "flexlinks.com", "ebayadservices.com",
    "rover.ebay.com", "shopzilla.com", "bizrate.com", "nextag.com", "pricegrabber.com", "kelkoo.com",
    "valuecommerce.com", "a8.net", "accesstrade.net", "moshimo.com", "afl.rakuten.co.jp",
    "clk.atdmt.com", "click.atdmt.com", "track.adform.net",
)
SHOP_RE = re.compile(r"^(ad[a-z-]*|googleads)\.([a-z0-9-]+\.)*doubleclick\.net$")

# Never blocked, whatever the list says: KantanOS's own updates and apps, and the blocker itself.
NEVER = ("ghcr.io", "github.com", "githubusercontent.com", "flathub.org", "flatpak.org",
         "fedoraproject.org", "someonewhocares.org", "quad9.net")

QUAD9 = ("9.9.9.9#dns.quad9.net 149.112.112.112#dns.quad9.net "
         "2620:fe::fe#dns.quad9.net 2620:fe::9#dns.quad9.net")
DNS_CONF = ("# KantanOS site blocker: safe look-up service (Quad9). Rewritten automatically;\n"
            "# turn it off in Block bad sites, not here.\n"
            "[Resolve]\nDNS=" + QUAD9 + "\nDNSOverTLS=opportunistic\nDomains=~.\n")

NAME = re.compile(r"^(?=.{4,253}$)(?:[a-z0-9_](?:[a-z0-9_-]{0,61}[a-z0-9_])?\.)+[a-z0-9-]{2,63}$")
ENTRY = re.compile(r"^(?:0\.0\.0\.0|127\.0\.0\.1)[ \t]+(\S+)")
TAG = re.compile(r"^#\s*<(/?)([A-Za-z0-9_-]+)>")
DATED = re.compile(r"^#\s*Last updated:\s*(.{5,60})$")


def under(name, domains):
    return any(name == d or name.endswith("." + d) for d in domains)


def valid(name):
    return bool(NAME.match(name)) and not name.replace(".", "").isdigit()


def normalise(text):
    """A site name from whatever someone typed or pasted (an address, a link); "" if it isn't one."""
    s = str(text or "").strip().lower()
    s = re.sub(r"^[a-z][a-z0-9+.-]*://", "", s)
    s = re.split(r"[/?#\s]", s, maxsplit=1)[0]
    s = s.rsplit("@", 1)[-1]
    s = re.sub(r":\d+$", "", s).strip(".")
    if s and not s.isascii():
        try:
            s = s.encode("idna").decode("ascii")
        except UnicodeError:
            return ""
    return s if valid(s) else ""


def parse_list(text):
    """The downloaded list → ({name: category}, the list's own date). Only names are kept."""
    names, stack, dated = {}, [], ""
    for line in text.splitlines():
        if line.startswith("#"):
            m = TAG.match(line)
            if m:
                if not m.group(1):
                    stack.append(m.group(2))
                elif m.group(2) in stack:
                    while stack and stack.pop() != m.group(2):
                        pass
            elif not dated:
                d = DATED.match(line)
                if d:
                    dated = re.sub(r"[^A-Za-z0-9,: ]", "", d.group(1)).strip()
            continue
        m = ENTRY.match(line)
        if not m or any(s in SKIP_SECTIONS for s in stack):
            continue
        name = m.group(1).lower().rstrip(".")
        if not valid(name) or under(name, NEVER) or name in names:
            continue
        cat = next((SECTIONS[s] for s in reversed(stack) if s in SECTIONS), "harm")
        if cat in ("ads", "spy") and (under(name, SHOP_SUFFIXES) or SHOP_RE.match(name)):
            cat = "shop"
        names[name] = cat
    return names, dated


def default_settings():
    return {"on": True, "categories": {c[0]: True for c in CATEGORIES}, "allow": [], "safe_dns": True}


def clean_settings(obj):
    """Settings from a file or from the window, with anything unexpected dropped."""
    s = default_settings()
    if not isinstance(obj, dict):
        return s
    for key in ("on", "safe_dns"):
        if isinstance(obj.get(key), bool):
            s[key] = obj[key]
    cats = obj.get("categories")
    if isinstance(cats, dict):
        for cid in s["categories"]:
            if isinstance(cats.get(cid), bool):
                s["categories"][cid] = cats[cid]
    allow = obj.get("allow")
    if isinstance(allow, list):
        seen = []
        for a in allow[:500]:
            n = normalise(a) if isinstance(a, str) else ""
            if n and n not in seen:
                seen.append(n)
        s["allow"] = sorted(seen)
    return s


def blocked_names(names, settings):
    """The names to refuse right now."""
    if not settings["on"]:
        return []
    on = {c for c, v in settings["categories"].items() if v}
    return sorted(n for n, c in names.items() if c in on and not under(n, settings["allow"]))


def look_up(site, names, settings):
    """What the list does with one site: {"name", "listed": category or "", "blocked", "allowed",
    "inside": how many addresses under it are on the list, "inside_cats"}."""
    name = normalise(site)
    if not name:
        return None
    exact = names.get(name) or names.get("www." + name) or ""
    inside = [(n, c) for n, c in names.items() if n.endswith("." + name)]
    now = set(blocked_names({n: c for n, c in names.items() if n == name or n == "www." + name
                             or n.endswith("." + name)}, settings))
    return {"name": name, "listed": exact, "blocked": name in now or "www." + name in now,
            "allowed": under(name, settings["allow"]), "inside": len(inside),
            "inside_blocked": len([n for n, _ in inside if n in now]),
            "inside_cats": sorted({c for _, c in inside}, key=list(TITLES).index)}


def site_of(name):
    """The name to put on the allow list so the whole site opens (www.shop.com → shop.com)."""
    return name[4:] if name.startswith("www.") and valid(name[4:]) else name


class Blocker:
    """Files and actions. `root` is "/" on a real PC; tests give a scratch folder."""

    def __init__(self, root="/"):
        self.root = root
        j = lambda *p: os.path.join(root, *p)
        self.settings_file = j("etc/kantanos/site-blocker.json")
        self.hosts = j("etc/hosts")
        self.dns_conf = j("etc/systemd/resolved.conf.d/90-kantanos-safe-dns.conf")
        self.var = j("var/lib/kantanos/site-blocker")
        self.list_file = os.path.join(self.var, "hosts")
        self.state_file = os.path.join(self.var, "state.json")
        self.real = os.path.abspath(root) == os.path.abspath(os.sep)

    # ---- reading (anyone) ----------------------------------------------------------------
    def settings(self):
        try:
            with open(self.settings_file, encoding="utf-8") as fh:
                return clean_settings(json.load(fh))
        except (OSError, ValueError):
            return default_settings()

    def state(self):
        try:
            with open(self.state_file, encoding="utf-8") as fh:
                s = json.load(fh)
            return s if isinstance(s, dict) else {}
        except (OSError, ValueError):
            return {}

    def names(self):
        try:
            with open(self.list_file, encoding="utf-8", errors="replace") as fh:
                return parse_list(fh.read())
        except OSError:
            return {}, ""

    def status(self):
        return {"settings": self.settings(), "state": self.state()}

    # ---- writing (root) ------------------------------------------------------------------
    def _write(self, path, text, mode=0o644):
        """Writes a whole file at once (a new file swapped in), so a power cut can't leave half."""
        path = os.path.realpath(path)                    # a link stays a link; its target is written
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".kantanos-", dir=os.path.dirname(path))
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            os.chmod(tmp, mode)
            try:
                os.replace(tmp, path)
            except OSError:
                # The file can't be swapped (it is mounted on its own, as inside a container):
                # write into it instead.
                with open(path, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(text)
                os.unlink(tmp)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def _run(self, *cmd):
        if not self.real:
            return
        try:
            subprocess.run(cmd, capture_output=True, timeout=60)
        except (OSError, subprocess.SubprocessError):
            pass

    def save_settings(self, settings):
        self._write(self.settings_file, json.dumps(clean_settings(settings), indent=1) + "\n")

    def fetch(self, opener=None):
        """Downloads the list and keeps it if it looks right. Returns "" or what went wrong."""
        try:
            if opener:
                raw, final = opener(LIST_URL)
            else:
                req = urllib.request.Request(LIST_URL, headers={"User-Agent": "KantanOS-site-blocker"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    final = r.geturl()
                    raw = r.read(MAX_BYTES + 1)
        except (OSError, ValueError) as e:
            return f"Couldn't fetch the list ({str(e)[:120]}). The last good copy stays in use."
        host = re.sub(r"^https://([^/:]+).*$", r"\1", final) if final.startswith("https://") else ""
        if not under(host, (LIST_HOST,)):
            return "The list came from an unexpected address, so it wasn't used."
        if len(raw) > MAX_BYTES:
            return "The list was far bigger than expected, so it wasn't used."
        text = raw.decode("utf-8", errors="replace")
        names, _ = parse_list(text)
        if len(names) < MIN_NAMES:
            return "The list looked broken (too few sites), so it wasn't used."
        self._write(self.list_file, text)
        return ""

    def stale(self):
        try:
            return time.time() - os.path.getmtime(self.list_file) > STALE
        except OSError:
            return True

    def apply(self, error=""):
        """Rewrites our part of /etc/hosts and the safe look-up setting from the settings."""
        settings = self.settings()
        names, dated = self.names()
        block = blocked_names(names, settings)
        try:
            with open(self.hosts, encoding="utf-8", errors="replace") as fh:
                old = fh.read()
        except OSError:
            old = "127.0.0.1 localhost\n::1 localhost\n"
        kept, inside = [], False
        for line in old.splitlines():
            if line.strip() == BEGIN:
                inside = True
            elif line.strip() == END:
                inside = False
            elif not inside:
                kept.append(line)
        while kept and not kept[-1].strip():
            kept.pop()
        new = "\n".join(kept) + "\n"
        if block:
            new += ("\n" + BEGIN + "\n"
                    "# Sites from Dan Pollock's list, https://someonewhocares.org/hosts/ (free for\n"
                    "# non-commercial use). To allow a site, use the Block bad sites window.\n"
                    + "".join(f"0.0.0.0 {n}\n" for n in block) + END + "\n")
        if new != old:
            self._write(self.hosts, new)
            self._run("restorecon", self.hosts)
            self._run("resolvectl", "flush-caches")

        try:
            with open(self.dns_conf, encoding="utf-8") as fh:
                had = fh.read()
        except OSError:
            had = None
        want = DNS_CONF if settings["safe_dns"] else None
        if want != had:
            if want is None:
                os.unlink(self.dns_conf)
            else:
                self._write(self.dns_conf, want)
                self._run("restorecon", self.dns_conf)
            self._run("systemctl", "try-reload-or-restart", "systemd-resolved.service")

        counts = {c[0]: 0 for c in CATEGORIES}
        for c in names.values():
            counts[c] += 1
        try:
            fetched = int(os.path.getmtime(self.list_file))
        except OSError:
            fetched = 0
        state = {"fetched": fetched, "list_date": dated, "counts": counts, "listed": len(names),
                 "blocked": len(block), "safe_dns": bool(settings["safe_dns"]), "error": error}
        self._write(self.state_file, json.dumps(state, indent=1) + "\n")
        return state

    def update(self, force=False, opener=None):
        """Fetch if the copy is old (or missing), then apply."""
        settings = self.settings()
        error = ""
        if settings["on"] and (force or self.stale()):
            error = self.fetch(opener)
        return self.apply(error)


def self_test():
    sample = "\n".join([
        "# Last updated: Sun, 22 Nov 2026 at 18:41:00 GMT",
        "#<localhost>", "127.0.0.1 localhost", "0.0.0.0 local", "#</localhost>",
        "#<malware-sites>", "0.0.0.0 bad-virus.example", "0.0.0.0 EVIL.Example.  # note",
        "6.6.6.6 bank.example", "0.0.0.0 github.com", "0.0.0.0 raw.githubusercontent.com",
        "0.0.0.0 not a name", "0.0.0.0 1.2.3.4", "#</malware-sites>",
        "#<spyware-sites>", "0.0.0.0 counter.example", "#<maybe-spy>", "0.0.0.0 maybe.example",
        "#</maybe-spy>", "0.0.0.0 after.example", "#</spyware-sites>",
        "#<ad-sites>", "0.0.0.0 ads.example", "0.0.0.0 www.googleadservices.com",
        "0.0.0.0 ad.doubleclick.net", "0.0.0.0 stats.g.doubleclick.net", "0.0.0.0 www.shareasale.com",
        "0.0.0.0 shareasale.com", "#</ad-sites>",
        "#<shock-sites>", "0.0.0.0 shock.example", "#</shock-sites>",
        "#<brand-new-section>", "0.0.0.0 unknown.example", "#</brand-new-section>",
    ] + [f"0.0.0.0 filler{i}.example" for i in range(MIN_NAMES)])
    names, dated = parse_list(sample)
    assert dated == "Sun, 22 Nov 2026 at 18:41:00 GMT", dated
    assert names["bad-virus.example"] == "harm" and names["evil.example"] == "harm"
    assert "bank.example" not in names and "github.com" not in names and "localhost" not in names
    assert "raw.githubusercontent.com" not in names and "1.2.3.4" not in names and "local" not in names
    assert names["counter.example"] == names["maybe.example"] == names["after.example"] == "spy"
    assert names["ads.example"] == "ads" and names["stats.g.doubleclick.net"] == "ads"
    assert names["www.googleadservices.com"] == names["ad.doubleclick.net"] == "shop"
    assert names["www.shareasale.com"] == "shop" and names["shock.example"] == "shock"
    assert names["unknown.example"] == "harm"

    assert normalise("https://WWW.Shop.Example:8443/deal?x=1") == "www.shop.example"
    assert normalise("shop.example/") == "shop.example" and normalise("hello") == "" and normalise("a b.com") == ""
    assert normalise("192.168.1.1") == "" and site_of("www.shop.example") == "shop.example"
    s = clean_settings({"on": True, "categories": {"shop": False, "made-up": True, "ads": "yes"},
                        "allow": ["HTTPS://Ads.Example/x", "ads.example", 7, "; rm -rf /", "x" * 300 + ".com"],
                        "safe_dns": False, "extra": 1})
    assert s["categories"] == {"harm": True, "shock": True, "spy": True, "ads": True, "shop": False}
    assert s["allow"] == ["ads.example"] and s["safe_dns"] is False and "extra" not in s
    b = blocked_names(names, s)
    assert "bad-virus.example" in b and "shock.example" in b and "stats.g.doubleclick.net" in b
    assert "ads.example" not in b and "www.shareasale.com" not in b and "ad.doubleclick.net" not in b
    assert blocked_names(names, dict(s, on=False)) == []
    hit = look_up("http://shareasale.com/r.cfm", names, default_settings())
    assert hit["listed"] == "shop" and hit["blocked"] and hit["inside"] == 1
    assert not look_up("shareasale.com", names, s)["blocked"]
    assert look_up("nothing.example", names, s)["listed"] == "" and look_up("??", names, s) is None

    with tempfile.TemporaryDirectory() as root:
        bl = Blocker(root)
        os.makedirs(os.path.join(root, "etc"))
        mine = "127.0.0.1 localhost\n192.168.1.20 printer   # my own line\n"
        with open(bl.hosts, "w", encoding="utf-8") as fh:
            fh.write(mine)
        assert bl.settings() == default_settings() and bl.stale()
        # a download from the wrong place, a broken one and an http one are all refused
        assert "unexpected" in bl.fetch(lambda u: (sample.encode(), "https://evil.example/hosts"))
        assert "unexpected" in bl.fetch(lambda u: (sample.encode(), "http://someonewhocares.org/hosts"))
        assert "broken" in bl.fetch(lambda u: (b"0.0.0.0 one.example\n", LIST_URL))
        assert not os.path.exists(bl.list_file)
        st = bl.update(opener=lambda u: (sample.encode(), LIST_URL))
        assert st["error"] == "" and st["listed"] == len(names) and st["blocked"] == len(names)
        assert st["counts"]["shop"] == 4 and st["counts"]["shock"] == 1
        text = open(bl.hosts, encoding="utf-8").read()
        assert text.startswith(mine) and "0.0.0.0 bad-virus.example\n" in text and "bank.example" not in text
        assert "6.6.6.6" not in text and text.count(BEGIN) == 1 and text.endswith(END + "\n")
        assert "dns.quad9.net" in open(bl.dns_conf, encoding="utf-8").read()
        # shop links off, one site allowed, safe look-up off; applying twice changes nothing more
        bl.save_settings({"categories": {"shop": False}, "allow": ["ads.example"], "safe_dns": False})
        st = bl.update(opener=lambda u: 1 / 0)             # the copy is fresh: no download at all
        assert st["blocked"] == len(names) - 5 and st["error"] == ""
        text = open(bl.hosts, encoding="utf-8").read()
        assert "shareasale" not in text and "ads.example" not in text
        assert "0.0.0.0 shock.example\n" in text and not os.path.exists(bl.dns_conf)
        bl.apply()
        assert open(bl.hosts, encoding="utf-8").read() == text and text.count(BEGIN) == 1
        # a failed fetch keeps the last good copy and says so
        st = bl.update(force=True, opener=lambda u: (_ for _ in ()).throw(OSError("no network")))
        assert "last good copy" in st["error"] and st["blocked"] == len(names) - 5
        # everything off: our part goes, the person's own lines stay
        bl.save_settings({"on": False, "safe_dns": False})
        bl.apply()
        assert open(bl.hosts, encoding="utf-8").read() == mine
    print("site blocker self-test ok")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
