"""KantanOS Watch TV: where channels come from and how they're sorted.

Sources (all free or the family's own):
  - Free TV: broadcasters from the iptv-org lists (channels.json, streams.json, feeds.json,
    blocklist.json at iptv-org.github.io/api). Blocked, adult, closed and geo-blocked streams
    are left out.
  - Pluto TV and Plex free channels, per country: the channel list and guide come from the
    XMLTV files at i.mjh.nz, the stream from jmp2.uk/<service>-<id>.m3u8.
  - The family's own provider: an M3U link (and XMLTV guide link) they paste in.

Sorting: every channel gets one country, one topic (News, Sports, Movies, ...) and sometimes a
sub-topic (TV shows -> Comedy, Drama, ...; Local stations -> the state). The same channel from
several sources becomes one channel with backup streams. Numbers come in cable-style blocks
per country (local stations 2-99, news 100s, sports 200s, ...) and never change once given.
"""
import collections
import gzip
import hashlib
import json
import os
import re
import time
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET

HOME = os.path.expanduser("~")
CACHE = os.path.join(os.environ.get("XDG_CACHE_HOME", os.path.join(HOME, ".cache")), "kantanos", "tv")
DATA = os.path.join(os.environ.get("XDG_DATA_HOME", os.path.join(HOME, ".local", "share")), "kantanos", "tv")
CONFIG = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.join(HOME, ".config")), "kantanos", "tv.json")
UA = "KantanOS-TV/1.0"
IPTV_ORG = "https://iptv-org.github.io/api/"

# Free services reachable from anywhere through jmp2.uk, with the countries they have guides for.
SERVICES = {
    "pluto": {"name": "Pluto TV", "guide": "https://i.mjh.nz/PlutoTV/{cc}.xml.gz", "stream": "https://jmp2.uk/plu-{id}.m3u8",
              "info": "https://i.mjh.nz/PlutoTV/.channels.json",
              "countries": "ar br ca cl de dk es fr gb it mx no se us".split()},
    "plex": {"name": "Plex", "guide": "https://i.mjh.nz/Plex/{cc}.xml.gz", "stream": "https://jmp2.uk/plex-{id}.m3u8",
             "countries": "au ca es fr gb mx nz us".split()},
}
# Samsung TV Plus streams don't open from outside its countries, but its channel groups are good,
# so they help sort the same channels coming from elsewhere (Plex has no groups at all).
SAMSUNG_INFO = "https://i.mjh.nz/SamsungTVPlus/.channels.json"

# A service's or provider's own group name -> (topic, sub-topic). First match wins.
GROUP_RULES = [
    (r"espa[nñ]ol|latino|spanish", ("languages", "Español")), (r"local news", ("local", "Local news")),
    (r"news|opinion|weather", ("news", None)), (r"motor ?sport", ("sports", "Motor sports")),
    (r"sport|outdoor", ("sports", None)), (r"music", ("music", None)), (r"kid|children|family", ("kids", None)),
    (r"ambian|relax|scenic|fireplace", ("life", "Relaxing scenes")), (r"home|food|lifestyle|travel", ("life", None)),
    (r"nature|history|science|documentar|animals", ("docs", None)),
    (r"true crime|^crime|mystery", ("shows", "Crime and mystery")), (r"competition|reality", ("shows", "Reality")),
    (r"game show|daytime", ("shows", "Game shows")), (r"classic", ("shows", "Classic TV")),
    (r"western", ("movies", "Westerns")), (r"sci-?fi", ("shows", "Sci-fi and fantasy")), (r"anime", ("shows", "Anime")),
    (r"comedy", ("shows", "Comedy")), (r"drama|action", ("shows", "Drama")), (r"movie|film|cinema", ("movies", None)),
    (r"season|holiday|christmas", ("shows", "Holiday")), (r"faith|relig", ("faith", None)), (r"shop", ("shopping", None)),
]
COMMUNITY = re.compile(r"\bchannel \d+|\baccess\b|civic|community|\bpeg\b|\btv \d+$|city tv|county tv|municipal|\bgov ?tv|educational access", re.I)
CALL_SIGN = re.compile(r"^[KW][A-Z]{2,3}(-(TV|DT|LD|CD|LP))?(\s|$)")

# Topics in channel-number order. Names are what the family sees.
TOPICS = [
    ("local", "Local stations"), ("news", "News"), ("sports", "Sports"), ("movies", "Movies"),
    ("shows", "TV shows"), ("kids", "Kids"), ("docs", "Documentaries"), ("music", "Music"),
    ("life", "Food, home and travel"), ("faith", "Faith"), ("shopping", "Shopping"),
    ("government", "Government"), ("languages", "Other languages"),
]
TOPIC_NAMES = dict(TOPICS)

# iptv-org categories -> topic. "general"/"entertainment" are weak hints, used last.
IPTV_TOPIC = {
    "news": "news", "business": "news", "weather": "news", "sports": "sports", "outdoor": "sports",
    "movies": "movies", "series": "shows", "comedy": "shows", "classic": "shows", "kids": "kids",
    "animation": "kids", "family": "kids", "documentary": "docs", "science": "docs", "education": "docs",
    "culture": "docs", "music": "music", "cooking": "life", "lifestyle": "life", "travel": "life",
    "auto": "life", "relax": "life", "woman": "life", "religious": "faith", "shop": "shopping",
    "legislative": "government", "public": "government",
}
WEAK = {"general": "shows", "entertainment": "shows", "interactive": "shows"}

# Programme categories in the guides -> topic (looked at over a whole channel's day).
EPG_TOPIC = [
    (r"^news|news &|current affairs|politic", "news"), (r"^sports?\b|football|basketball|soccer|hockey", "sports"),
    (r"^movies?$|^film$|feature film", "movies"), (r"children|kids|preschool|animated|cartoon", "kids"),
    (r"documentar|nature|science|history|educational", "docs"), (r"^music", "music"),
    (r"food|cooking|home &|lifestyle|travel|garden|diy|fashion", "life"), (r"religio|faith|spiritual", "faith"),
    (r"shopping|infomercial", "shopping"),
]
NAME_TOPIC = [
    (r"\bnews|noticias|nachrichten|cbc news|cnn|bloomberg|cnbc|newsmax|\bnhk world|weather", "news"),
    (r"sports?\b|deportes|\bnfl\b|\bnba\b|\bnhl\b|\bmlb\b|golf|fight|boxing|wrestling|\bufc\b|racing|poker|fishing|hunting|outdoor", "sports"),
    (r"movies?\b|cinema|\bcine\b|films?\b|\bflix\b|westerns?\b|horror|scream|scares?\b|fright|shudder", "movies"),
    (r"\bkids?\b|junior|cartoon|toons?\b|nick\b|nickelodeon|baby|preschool|anime kids|sesame|teletubbies|paw patrol|pbs kids", "kids"),
    (r"documentar|history|nature|science|wild|planet|discovery|nasa|smithsonian|curiosity", "docs"),
    (r"music|\bmtv\b|\bhits\b|radio\b|concert|karaoke|\bvevo\b|country\b|jazz|classical|\bxite\b", "music"),
    (r"cook|food|kitchen|chef|home\b|garden|travel|\bdiy\b|lifestyle|fashion|tastemade|\bhgtv\b", "life"),
    (r"church|gospel|christian|faith|catholic|\bewtn\b|bible|\bgod\b|islam|quran|hope\b|\b3abn\b|\btbn\b|daystar", "faith"),
    (r"\bqvc\b|\bhsn\b|shop|jewelry", "shopping"),
    (r"senate|house of rep|council|legislat|parliament|\bcpac\b|c-span|government|city of |county", "government"),
]
# Sub-topics, so a few hundred "TV shows" or "Movies" channels become short lists.
SHOW_SUBS = [
    (r"comedy|sitcom|laugh|funny", "Comedy"), (r"crime|mystery|detective|thriller|csi|law|police|true crime|forensic", "Crime and mystery"),
    (r"reality|human interest|dating|real housewives|survivor|bravo", "Reality"),
    (r"sci-?fi|science fiction|fantasy|star trek|doctor who|stargate", "Sci-fi and fantasy"),
    (r"anime", "Anime"), (r"game show|quiz|\bfeud\b|jeopardy|wheel", "Game shows"),
    (r"classic|retro|\b(19)?[5-8]0s\b|western", "Classic TV"), (r"drama|soap|novela", "Drama"),
]
MOVIE_SUBS = [
    (r"action|adventure", "Action"), (r"horror|scream|terror|fright", "Horror"), (r"comedy|laugh", "Comedy"),
    (r"western", "Westerns"), (r"classic|retro|vintage", "Classics"), (r"family|kids", "Family"),
    (r"romance|love|hallmark", "Romance"), (r"thriller|crime|mystery", "Thrillers"), (r"sci-?fi|science fiction", "Sci-fi"),
]
SPANISH_HINTS = re.compile(r"\b(en español|espanol|español|latino|cine |novelas?|telemundo|univision|unimas|"
                           r"estrella|azteca|televisa|caracol|clásic|series latinas|comedia|acción|infantil|noticias|"
                           r"telenovelas?|canela|naturaleza|lucha|cocina|películas|peliculas|clasicos|historias)\b", re.I)
LANG_NAMES = {"spa": "Español", "fra": "Français", "deu": "Deutsch", "por": "Português", "ita": "Italiano",
              "jpn": "日本語", "kor": "한국어", "zho": "中文", "vie": "Tiếng Việt", "hin": "हिन्दी", "ara": "العربية",
              "rus": "Русский", "pol": "Polski", "tgl": "Tagalog", "eng": "English"}
COUNTRY_LANGS = {"US": {"eng"}, "CA": {"eng", "fra"}, "GB": {"eng"}, "AU": {"eng"}, "NZ": {"eng"}, "IE": {"eng"},
                 "JP": {"jpn"}, "FR": {"fra"}, "DE": {"deu"}, "ES": {"spa"}, "MX": {"spa"}, "IT": {"ita"},
                 "BR": {"por"}, "AR": {"spa"}, "CL": {"spa"}, "IN": {"hin", "eng"}, "KR": {"kor"}}
# Languages spoken mostly in one country: channels in them broadcast from elsewhere (NHK World,
# Japanese channels relayed abroad) join that country's list too.
LANGUAGE_HOME = {"JP": "jpn", "KR": "kor"}
US_STATES = {"AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California", "CO": "Colorado",
             "CT": "Connecticut", "DE": "Delaware", "DC": "Washington DC", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
             "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana",
             "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
             "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
             "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
             "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
             "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
             "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming", "PR": "Puerto Rico"}
CA_PROVINCES = {"AB": "Alberta", "BC": "British Columbia", "MB": "Manitoba", "NB": "New Brunswick", "NL": "Newfoundland",
                "NS": "Nova Scotia", "ON": "Ontario", "PE": "Prince Edward Island", "QC": "Québec", "SK": "Saskatchewan",
                "NT": "Northwest Territories", "NU": "Nunavut", "YT": "Yukon"}


# ---- settings ------------------------------------------------------------------------------
DEFAULTS = {"countries": ["US"], "services": {"freetv": True, "pluto": True, "plex": True},
            "providers": [], "record_dir": os.path.join(HOME, "Videos", "TV recordings"),
            "show_broken": False}


def load_config():
    cfg = json.loads(json.dumps(DEFAULTS))
    try:
        with open(CONFIG, encoding="utf-8") as f:
            cfg.update(json.load(f))
    except (OSError, ValueError):
        pass
    return cfg


def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
    tmp = CONFIG + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)   # provider links can hold a login
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=1, ensure_ascii=False)
    os.replace(tmp, CONFIG)


# ---- downloads with a cache ----------------------------------------------------------------
def cache_path(url):
    tail = re.sub(r"[^A-Za-z0-9.]+", "_", url.split("://", 1)[-1])[-60:]
    return os.path.join(CACHE, hashlib.sha1(url.encode()).hexdigest()[:10] + "-" + tail)


def fetch(url, max_age=24 * 3600, timeout=60):
    """The file at url (bytes), from the cache when it's fresh enough. Falls back to an old copy
    when the internet is down; raises OSError when there's neither."""
    path = cache_path(url)
    try:
        if time.time() - os.path.getmtime(path) < max_age:
            with open(path, "rb") as f:
                return f.read()
    except OSError:
        pass
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
        if url.endswith(".gz") or data[:2] == b"\x1f\x8b":
            data = gzip.decompress(data)
        os.makedirs(CACHE, exist_ok=True)
        with open(path + ".tmp", "wb") as f:
            f.write(data)
        os.replace(path + ".tmp", path)
        return data
    except OSError:
        with open(path, "rb") as f:             # old copy, or OSError if there isn't one
            return f.read()


def fetch_json(name):
    return json.loads(fetch(IPTV_ORG + name + ".json"))


# ---- helpers -------------------------------------------------------------------------------
def norm(name):
    """A name reduced so the same channel from two places matches: "Pluto TV Crime Drama" and
    "Crime Drama"; "CBS News 24/7" and "CBS News 24-7 HD"."""
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    n = re.sub(r"^(pluto tv|plex)\s+", "", n)
    n = re.sub(r"\b(hd|sd|fhd|uhd|4k|tv channel|channel|by plex|on plex)\b", " ", n)
    n = re.sub(r"\(.*?\)|\[.*?\]", " ", n)
    return re.sub(r"[^a-z0-9]+", "", n) or re.sub(r"\s+", "", name.lower())


def first_match(rules, text):
    for pat, val in rules:
        if re.search(pat, text, re.I):
            return val
    return None


def classify(name, iptv_cats=(), epg_cats=None, group=""):
    """(topic, sub-topic) for a channel. The service's own group wins (Pluto's "True Crime"),
    then iptv-org's categories, then what its programmes are mostly about, then its name."""
    topic = sub = None
    if group:
        hit = first_match(GROUP_RULES, group)
        if hit:
            topic, sub = hit
    for c in ([] if topic else iptv_cats):
        if c in IPTV_TOPIC:
            topic = IPTV_TOPIC[c]
            break
    epg_text = ""
    if epg_cats:
        total = sum(epg_cats.values())
        votes = collections.Counter()
        for cat, n in epg_cats.items():
            t = first_match(EPG_TOPIC, cat)
            if t:
                votes[t] += n
        epg_text = " ".join(c for c, _ in epg_cats.most_common(6))
        if not topic and votes:
            t, n = votes.most_common(1)[0]
            if n >= 0.4 * total:
                topic = t
    if not topic:
        topic = first_match(NAME_TOPIC, name) or first_match(NAME_TOPIC, group or "")
    if not topic:
        for c in iptv_cats:
            if c in WEAK:
                topic = WEAK[c]
                break
    topic = topic or "shows"
    if sub:
        return topic, sub
    hint = f"{name} {' '.join(iptv_cats)} {epg_text}"
    if topic == "shows":
        sub = first_match(SHOW_SUBS, name) or first_match(SHOW_SUBS, hint) or "More shows"
    elif topic == "movies":
        sub = first_match(MOVIE_SUBS, name) or first_match(MOVIE_SUBS, hint) or "All movies"
    return topic, sub


def read_guide_channels(xml_bytes):
    """{id: (name, icon, Counter of programme categories)} from an XMLTV file."""
    out, cats = {}, collections.defaultdict(collections.Counter)
    titles = collections.defaultdict(collections.Counter)
    for _, el in ET.iterparse(__import__("io").BytesIO(xml_bytes), events=("end",)):
        if el.tag == "channel":
            name = (el.findtext("display-name") or "").strip()
            icon = el.find("icon")
            out[el.get("id")] = [name, icon.get("src") if icon is not None else ""]
            el.clear()
        elif el.tag == "programme":
            cid = el.get("channel")
            for c in el.findall("category"):
                if c.text:
                    cats[cid][c.text.strip()] += 1
            titles[cid][(el.findtext("title") or "").strip().lower()] += 1
            el.clear()
    return {k: (v[0], v[1], cats.get(k, collections.Counter()), titles.get(k, collections.Counter()))
            for k, v in out.items()}


def one_show(titles):
    """True when a channel's guide is (nearly) one series all day: Baywatch, Duck Dynasty, ..."""
    total = sum(titles.values())
    return total >= 6 and titles.most_common(1)[0][1] >= 0.75 * total


NETWORK = re.compile(r"\bby ([A-Z][\w&+!.' ]{1,24})$")


# ---- building the lineup -------------------------------------------------------------------
class Lineup:
    def __init__(self, cfg=None, log=print):
        self.cfg = cfg or load_config()
        self.log = log
        self.channels = []          # list of dicts, see add()
        self.by_key = {}
        self.guides = []            # XMLTV links the guide reader should load
        self.errors = []
        self.groups, self.info = {}, {}

    def add(self, country, name, url, *, service, logo="", topic=None, sub=None, lang=None, epg=None,
            ua=None, ref=None, not247=False, quality=None, area=None):
        key = f"{country}:{norm(name)}"
        stream = {"url": url, "ua": ua, "ref": ref, "service": service, "quality": quality}
        c = self.by_key.get(key)
        if c:                       # same channel again: keep one, with this as a backup stream
            if url not in (s["url"] for s in c["streams"]):
                c["streams"].append(stream)
            if epg and epg not in c["epg"]:
                c["epg"].append(epg)
            c["logo"] = c["logo"] or logo
            return c
        c = {"key": key, "country": country, "name": name, "logo": logo, "topic": topic or "shows", "sub": sub,
             "lang": lang, "streams": [stream], "epg": [epg] if epg else [], "not247": not247, "area": area,
             "number": None}
        self.channels.append(c)
        self.by_key[key] = c
        return c

    def build(self):
        countries = [c.upper() for c in self.cfg.get("countries", [])]
        svc = self.cfg.get("services", {})
        meta = None
        if svc.get("freetv", True) or svc.get("pluto", True) or svc.get("plex", True):
            try:
                meta = self.iptv_meta()
            except (OSError, ValueError) as e:
                self.errors.append(f"Free TV list: {e}")
        self.info = {}
        for sid, url in (("pluto", SERVICES["pluto"]["info"]), ("samsung", SAMSUNG_INFO)):
            try:
                self.info[sid] = json.loads(fetch(url))["regions"]
            except (OSError, ValueError, KeyError):
                self.info[sid] = {}
        for cc in countries:
            self.groups = {}             # norm(name) -> group, from Samsung and Pluto, to sort others
            for sid in ("samsung", "pluto"):
                for ch in self.info[sid].get(cc.lower(), {}).get("channels", {}).values():
                    if ch.get("group"):
                        self.groups.setdefault(norm(ch["name"]), ch["group"])
            for sid in ("pluto", "plex"):
                if svc.get(sid, True) and cc.lower() in SERVICES[sid]["countries"]:
                    try:
                        self.add_service(sid, cc, meta)
                    except (OSError, ValueError, ET.ParseError) as e:
                        self.errors.append(f"{SERVICES[sid]['name']} {cc}: {e}")
            if svc.get("freetv", True) and meta:
                self.add_free_tv(cc, meta)
        for p in self.cfg.get("providers", []):
            try:
                self.add_provider(p)
            except (OSError, ValueError) as e:
                self.errors.append(f"{p.get('name') or 'Provider'}: {e}")
        self.place_languages()
        self.number()
        return self

    # iptv-org ---------------------------------------------------------------------------------
    def iptv_meta(self):
        try:
            self.countries_info = fetch_json("countries")
        except (OSError, ValueError):
            self.countries_info = []
        ch = {c["id"]: c for c in fetch_json("channels")}
        blocked = {b["channel"] for b in fetch_json("blocklist")}
        feeds = collections.defaultdict(list)
        for f in fetch_json("feeds"):
            feeds[f["channel"]].append(f)
        streams = fetch_json("streams")
        by_service_id = {}
        for s in streams:
            m = re.search(r"jmp2\.uk/(plu|plex)-([^.?/]+)", s["url"])
            if m and s.get("channel"):
                by_service_id[m.group(2)] = s["channel"]
        return {"channels": ch, "blocked": blocked, "feeds": feeds, "streams": streams, "service_ids": by_service_id}

    def feed_info(self, meta, cid, feed_id=None):
        fl = meta["feeds"].get(cid, [])
        f = next((x for x in fl if x["id"] == feed_id), None) or next((x for x in fl if x.get("is_main")), None) \
            or (fl[0] if fl else None)
        if not f:
            return None, None
        langs = f.get("languages") or []
        area = None
        for a in f.get("broadcast_area") or []:
            if a.startswith(("s/", "ct/")):          # a state/province or a city: a local station
                area = a.split("/", 1)[1]
                break
        return (langs[0] if langs else None), area

    @staticmethod
    def feed_langs(meta, cid, feed_id=None):
        fl = meta["feeds"].get(cid, [])
        f = next((x for x in fl if x["id"] == feed_id), None) if feed_id else None
        return (f or {}).get("languages") or [lang for x in fl for lang in (x.get("languages") or [])]

    def add_free_tv(self, cc, meta):
        n = 0
        selected = {x.upper() for x in self.cfg.get("countries", [])}
        also = LANGUAGE_HOME.get(cc)        # e.g. Japan also gets Japanese channels broadcast from abroad
        for s in meta["streams"]:
            cid = s.get("channel")
            c = meta["channels"].get(cid) if cid else None
            if not c or cid in meta["blocked"]:
                continue
            if c.get("country") != cc:
                if not also or c.get("country") in selected or also not in self.feed_langs(meta, cid, s.get("feed")):
                    continue
            if c.get("is_nsfw") or c.get("closed") or "xxx" in (c.get("categories") or []):
                continue
            labels = s.get("labels") or []
            if "Geo-blocked" in labels or re.search(r"jmp2\.uk/(plu|plex)-", s["url"]):
                continue                                   # services are added from their own guides
            lang, area = self.feed_info(meta, cid, s.get("feed"))
            if c.get("country") != cc:
                lang, area = also, None              # joined for its language: it's at home here
            cats = c.get("categories") or []
            strong = any(x in IPTV_TOPIC for x in cats)
            topic, sub = classify(c["name"], cats, None, "" if strong else self.groups.get(norm(c["name"]), ""))
            general = set(cats) & {"general", "news", "entertainment", "public", "legislative"} or not cats
            if topic in ("shows", "news", "government") and general:
                place = self.area_name(cc, area) if area else None
                if place or CALL_SIGN.match(c["name"]):
                    topic, sub = "local", place or "More local stations"
                elif COMMUNITY.search(c["name"]):
                    topic, sub = "local", "Community TV"
            self.add(cc, c["name"], s["url"], service="Free TV", topic=topic, sub=sub, lang=lang,
                     epg=("iptv-org", cid), ua=s.get("user_agent"), ref=s.get("referrer"),
                     not247="Not 24/7" in labels, quality=s.get("quality"), area=area)
            n += 1
        self.log(f"Free TV {cc}: {n} streams")

    @staticmethod
    def area_name(cc, area):
        code = area.split("-", 1)[-1].split("-")[0] if "-" in area else ""
        if cc == "US":
            return US_STATES.get(code)
        if cc == "CA":
            return CA_PROVINCES.get(code)
        return None

    # Pluto TV / Plex -------------------------------------------------------------------------
    def add_service(self, sid, cc, meta):
        s = SERVICES[sid]
        guide = s["guide"].format(cc=cc.lower())
        chans = read_guide_channels(fetch(guide, max_age=6 * 3600))
        self.guides.append(guide)
        for gid, (name, icon, cats, titles) in chans.items():
            if not name:
                continue
            iptv_cats, lang = [], None
            cid = (meta or {}).get("service_ids", {}).get(gid)
            if cid and cid in meta["channels"]:
                iptv_cats = meta["channels"][cid].get("categories") or []
                lang, _ = self.feed_info(meta, cid)
            if "xxx" in iptv_cats:
                continue
            clean = re.sub(r"^(Pluto TV|Plex)\s+", "", name).strip() or name
            group = (self.info.get(sid, {}).get(cc.lower(), {}).get("channels", {}).get(gid) or {}).get("group") \
                or self.groups.get(norm(clean), "")
            topic, sub = classify(clean, iptv_cats, cats, group)
            if topic == "shows" and sub == "More shows":
                net = NETWORK.search(clean)
                sub = "One show all day" if one_show(titles) else (f"From {net.group(1).strip()}" if net else sub)
            if not lang and cc == "US" and (SPANISH_HINTS.search(name) or re.search("[áéíóúñ¿¡]", name)):
                lang = "spa"
            self.add(cc, clean, s["stream"].format(id=gid), service=s["name"], logo=icon, topic=topic, sub=sub,
                     lang=lang, epg=(guide, gid))
        self.log(f"{s['name']} {cc}: {len(chans)} channels")

    # the family's own provider ---------------------------------------------------------------
    def add_provider(self, p):
        name = p.get("name") or "My provider"
        text = fetch(p["m3u"], max_age=3 * 3600).decode("utf-8", "replace")
        if p.get("xmltv"):
            self.guides.append(p["xmltv"])
        n = 0
        info = None
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("#EXTINF"):
                info = line
            elif line and not line.startswith("#") and info:
                attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', info))
                title = info.rsplit(",", 1)[-1].strip()
                group = attrs.get("group-title", "")
                info = None
                if re.search(r"\bvod\b|movies? vod|series vod|24/7 vod", group, re.I) or re.search(r"\.(mp4|mkv|avi)$", line):
                    continue                                # films on demand aren't live channels
                topic, sub = classify(title, (), None, group)
                c = self.add(name, title, line, service=name, logo=attrs.get("tvg-logo", ""), topic=topic,
                             sub=sub or group or None, epg=(p.get("xmltv"), attrs.get("tvg-id")) if attrs.get("tvg-id") else None)
                c["group"] = group
                n += 1
        self.log(f"{name}: {n} channels")

    # sorting and numbers ---------------------------------------------------------------------
    def place_languages(self):
        """Channels in a language the country doesn't mainly speak get their own shelf
        ("Other languages" -> "Español"), so the main lists stay readable."""
        langs = {x["code"]: set(x.get("languages") or []) for x in getattr(self, "countries_info", [])}
        for c in self.channels:
            home = COUNTRY_LANGS.get(c["country"]) or langs.get(c["country"])
            if home and c["lang"] and c["lang"] not in home and c["topic"] != "local":
                c["topic"], c["sub"] = "languages", LANG_NAMES.get(c["lang"], c["lang"])
        # "From A&E" style shelves only when a family has a few channels.
        fam = collections.Counter((c["country"], c["sub"]) for c in self.channels if (c["sub"] or "").startswith("From "))
        for c in self.channels:
            if (c["sub"] or "").startswith("From ") and fam[(c["country"], c["sub"])] < 3:
                c["sub"] = "More shows"
        # Languages with only a couple of channels share one shelf.
        count = collections.Counter((c["country"], c["sub"]) for c in self.channels if c["topic"] == "languages")
        for c in self.channels:
            if c["topic"] == "languages" and (count[(c["country"], c["sub"])] < 3 or c["sub"] not in LANG_NAMES.values()):
                c["sub"] = "More languages"

    def number(self):
        path = os.path.join(DATA, "numbers.json")
        try:
            with open(path, encoding="utf-8") as f:
                saved = json.load(f)
        except (OSError, ValueError):
            saved = {}
        order = [t for t, _ in TOPICS]
        by_country = collections.defaultdict(list)
        for c in self.channels:
            by_country[c["country"]].append(c)
        for cc, chans in by_country.items():
            mine = saved.setdefault(cc, {})
            # Block for each topic: local 2-99, then 100 per topic (more when a topic is bigger).
            blocks, start = {}, 100
            sizes = collections.Counter(c["topic"] for c in chans)
            for t in order:
                if t == "local":
                    hi = 99 if sizes[t] <= 98 else (2 + sizes[t] + 99) // 100 * 100 - 1
                    blocks[t] = (2, hi)
                    start = hi + 1
                    continue
                span = max(100, (sizes[t] + 99) // 100 * 100)
                blocks[t] = (start, start + span - 1)
                start += span
            used = set()
            fresh = []
            for c in chans:
                n = mine.get(c["key"])
                lo, hi = blocks[c["topic"]]
                if isinstance(n, int) and lo <= n <= hi and n not in used:
                    c["number"] = n
                    used.add(n)
                else:
                    fresh.append(c)
            fresh.sort(key=lambda c: (order.index(c["topic"]), c["sub"] or "", c["name"].lower()))
            for c in fresh:
                lo, hi = blocks[c["topic"]]
                n = lo
                while n in used:
                    n += 1
                c["number"] = n
                used.add(n)
                mine[c["key"]] = n
        os.makedirs(DATA, exist_ok=True)
        with open(path + ".tmp", "w", encoding="utf-8") as f:
            json.dump(saved, f)
        os.replace(path + ".tmp", path)
        self.channels.sort(key=lambda c: (c["country"], c["number"]))

    # what the screens show -------------------------------------------------------------------
    def countries(self):
        seen = []
        for c in self.channels:
            if c["country"] not in seen:
                seen.append(c["country"])
        return seen

    def shelves(self, country):
        """[(topic, name, [(sub or None, count)], count)] for one country, in number order."""
        out = []
        chans = [c for c in self.channels if c["country"] == country]
        for t, label in TOPICS:
            here = [c for c in chans if c["topic"] == t]
            if not here:
                continue
            subs = collections.Counter(c["sub"] for c in here if c["sub"])
            out.append((t, label, sorted(subs.items()), len(here)))
        return out

    def pick(self, country=None, topic=None, sub=None, service=None, query=None):
        q = norm(query) if query else None
        return [c for c in self.channels
                if (not country or c["country"] == country) and (not topic or c["topic"] == topic)
                and (not sub or c["sub"] == sub)
                and (not service or any(s["service"] == service for s in c["streams"]))
                and (not q or q in norm(c["name"]))]


def country_list(max_age=7 * 86400):
    """Every country that has free channels: [{code, name, flag, streams, guide}], by name.
    "guide" means Pluto TV or Plex (with a full programme guide) cover it."""
    path = os.path.join(DATA, "countries.json")
    try:
        if time.time() - os.path.getmtime(path) < max_age:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    except (OSError, ValueError):
        pass
    info = fetch_json("countries")
    where = {c["id"]: c["country"] for c in fetch_json("channels") if not c.get("is_nsfw") and not c.get("closed")}
    n = collections.Counter(where.get(s.get("channel")) for s in fetch_json("streams")
                            if "Geo-blocked" not in (s.get("labels") or []))
    guided = {cc.upper() for s in SERVICES.values() for cc in s["countries"]}
    out = sorted(({"code": x["code"], "name": x["name"], "flag": x.get("flag", ""), "streams": n.get(x["code"], 0),
                   "guide": x["code"] in guided} for x in info if n.get(x["code"]) or x["code"] in guided),
                 key=lambda x: unicodedata.normalize("NFKD", x["name"]).lower())
    os.makedirs(DATA, exist_ok=True)
    with open(path + ".tmp", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    os.replace(path + ".tmp", path)
    return out


def wildcard(text):
    """A search the family types -> a regular expression. "star*" = starts with "star",
    "*news*" or plain "news" = has "news" in it, "?" = any one letter. Case and accents don't matter."""
    t = fold(text.strip())
    if not t:
        return None
    if "*" not in t and "?" not in t:
        return re.compile(re.escape(t))
    pat = re.escape(t).replace(r"\*", ".*").replace(r"\?", ".")
    return re.compile("^" + pat + "$")


def fold(s):
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()


def search_channels(lu, text, countries=None):
    rx = wildcard(text)
    if not rx:
        return []
    return [c for c in lu.channels if (not countries or c["country"] in countries) and rx.search(fold(c["name"]))]


def save_lineup(lineup):
    os.makedirs(DATA, exist_ok=True)
    path = os.path.join(DATA, "lineup.json")
    with open(path + ".tmp", "w", encoding="utf-8") as f:
        json.dump({"made": time.time(), "channels": lineup.channels, "guides": lineup.guides,
                   "errors": lineup.errors}, f, ensure_ascii=False)
    os.replace(path + ".tmp", path)


def load_saved():
    try:
        with open(os.path.join(DATA, "lineup.json"), encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return None
    lu = Lineup(log=lambda *a: None)
    lu.channels, lu.guides, lu.errors = d["channels"], d["guides"], d.get("errors", [])
    lu.by_key = {c["key"]: c for c in lu.channels}
    lu.made = d.get("made", 0)
    return lu


def self_test():
    assert norm("Pluto TV Crime Drama") == norm("Crime Drama")
    assert norm("CBS News 24/7 HD") == norm("CBS News 24/7")
    assert classify("Pluto TV Westerns")[0] == "movies"
    assert classify("ABC News Live", ["news"]) == ("news", None)
    assert classify("Paddington", [], collections.Counter({"Series": 5, "Children": 5}))[0] == "kids"
    assert classify("Star Trek", [], collections.Counter({"Series": 9, "Science fiction": 4})) == ("shows", "Sci-fi and fantasy")
    assert classify("Random Channel") == ("shows", "More shows")
    assert Lineup.area_name("US", "US-CA") == "California"
    lu = Lineup({"countries": [], "services": {}, "providers": []}, log=lambda *a: None)
    lu.add("US", "CBS News 24/7", "a", service="Pluto TV", topic="news")
    lu.add("US", "CBS News 24/7 HD", "b", service="Free TV", topic="news")
    assert len(lu.channels) == 1 and len(lu.channels[0]["streams"]) == 2
    lu.add("US", "Pluto TV Cine Terror", "c", service="Pluto TV", topic="movies", lang="spa")
    lu.place_languages()
    assert lu.by_key["US:" + norm("Cine Terror")]["topic"] == "languages"
    lu.add("US", "Star Trek", "d", service="Pluto TV")
    lu.add("US", "Star Wars Fans", "e", service="Pluto TV")
    lu.add("US", "Classic Star Trek Café", "f", service="Plex")
    names = lambda q: sorted(c["name"] for c in search_channels(lu, q))  # noqa: E731
    assert names("star*") == ["Star Trek", "Star Wars Fans"]
    assert names("*trek*") == names("TREK") == ["Classic Star Trek Café", "Star Trek"]
    assert names("*cafe") == ["Classic Star Trek Café"] and names("st?r trek") == ["Star Trek"]
    assert wildcard("  ") is None
    print("lineup self-test ok")


if __name__ == "__main__":
    import sys
    if "--self-test" in sys.argv:
        self_test()
    else:
        cfg = load_config()
        if len(sys.argv) > 1:
            cfg["countries"] = [a.upper() for a in sys.argv[1:]]
        lu = Lineup(cfg).build()
        for cc in lu.countries():
            print(f"\n== {cc}: {len(lu.pick(cc))} channels")
            for t, label, subs, n in lu.shelves(cc):
                nums = [c["number"] for c in lu.pick(cc, t)]
                print(f"  {label:<24}{n:>4}   {min(nums)}-{max(nums)}   " + ", ".join(f"{s} {k}" for s, k in subs[:12]))
        for e in lu.errors:
            print("problem:", e)
