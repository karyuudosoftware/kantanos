"""Shared AI and voice for KantanOS's everyday AI apps (Letters and documents, and the photo
and recipe helpers that follow).

The AI settings are the Helper's (~/.config/kantanos/helper.json): Ollama on this PC by default
(the same model the Helper and Kan-chan use), or an online service the person chose there. The
apps ask before anything is sent to an online service; on this PC nothing leaves it.

Voice: Piper on this PC, the voice chosen in the Helper (downloaded once, about 60 MB).
"""
import base64
import json
import math
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.parse
import urllib.request

HOME = os.path.expanduser("~")
CONF = os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.join(HOME, ".config")), "kantanos", "helper.json")
DATA = os.path.join(os.environ.get("XDG_DATA_HOME", os.path.join(HOME, ".local", "share")), "kantanos", "helper")
OLLAMA = os.environ.get("KANTAN_OLLAMA", "http://127.0.0.1:11434")
OLLAMA_UNIT = "kantanos-ollama.service"
VOICE_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
DEFAULT_VOICE = "en_US-hfc_female-medium"


# ---- settings -----------------------------------------------------------------------------
def settings():
    try:
        with open(CONF, encoding="utf-8") as f:
            cfg = json.load(f)
        return cfg if isinstance(cfg, dict) else {"provider": "local"}
    except (OSError, ValueError):
        return {"provider": "local"}


def save_settings(cfg):
    os.makedirs(os.path.dirname(CONF), exist_ok=True)
    fd = os.open(CONF + ".tmp", os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)   # may hold an API key
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=1)
    os.replace(CONF + ".tmp", CONF)


def online_host(cfg):
    """The online service's name (e.g. 'openrouter.ai') when the AI is online, else ''."""
    if cfg.get("provider") == "online" and cfg.get("online_url"):
        return urllib.parse.urlsplit(cfg["online_url"]).hostname or cfg["online_url"]
    return ""


def pick_local_model():
    """(model, download size) that fits the graphics card: Gemma 3 12B with 14 GB of video
    memory or more, else Gemma 3 4B. Both read pictures as well as text."""
    vram = 0
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=10).stdout
        vram = max(int(x) for x in out.split()) if out.strip() else 0
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    if not vram:
        import glob
        for p in glob.glob("/sys/class/drm/card*/device/mem_info_vram_total"):
            try:
                vram = max(vram, int(open(p).read()) // (1024 * 1024))
            except (OSError, ValueError):
                pass
    return ("gemma3:12b", "about 8 GB") if vram >= 14000 else ("gemma3:4b", "about 3 GB")


def local_model(cfg):
    return cfg.get("local_model") or pick_local_model()[0]


# ---- Ollama on this PC ------------------------------------------------------------------------
def _json(url, body=None, timeout=30):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def ollama_up():
    try:
        _json(OLLAMA + "/api/version", timeout=3)
        return True
    except (OSError, ValueError):
        return False


def start_ollama(wait=30):
    if ollama_up():
        return True
    subprocess.run(["systemctl", "--user", "start", OLLAMA_UNIT], capture_output=True)
    for _ in range(wait):
        if ollama_up():
            return True
        threading.Event().wait(1)
    return False


def model_ready(model):
    try:
        names = {m.get("name", "") for m in _json(OLLAMA + "/api/tags", timeout=5).get("models", [])}
    except (OSError, ValueError):
        return False
    return model in names or model + ":latest" in names


def pull(model, progress=None):
    """Download a model (once). progress(percent) while it runs. Raises on failure."""
    req = urllib.request.Request(OLLAMA + "/api/pull", data=json.dumps({"model": model}).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=3600) as r:
        for line in r:
            msg = json.loads(line)
            if msg.get("error"):
                raise RuntimeError(msg["error"])
            if msg.get("total") and progress:
                progress(int(msg.get("completed", 0) * 100 // msg["total"]))


def ai_ready(cfg):
    """'' when the AI can answer now; otherwise why not ('download' or 'offline')."""
    if online_host(cfg):
        return ""
    if not start_ollama():
        return "offline"
    return "" if model_ready(local_model(cfg)) else "download"


# ---- asking -----------------------------------------------------------------------------------
def chat(cfg, messages, json_mode=False, images=(), context=16384, temperature=0.3, timeout=900):
    """Ask the AI. images: picture files or bytes, attached to the last message."""
    pics = []
    for im in images:
        raw = im if isinstance(im, (bytes, bytearray)) else open(im, "rb").read()
        pics.append(base64.b64encode(raw).decode())
    if online_host(cfg):
        msgs = [dict(m) for m in messages]
        if pics:
            msgs[-1]["content"] = [{"type": "text", "text": msgs[-1]["content"]}] + [
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + p}} for p in pics]
        body = {"model": cfg.get("online_model", ""), "messages": msgs, "temperature": temperature}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        req = urllib.request.Request(cfg["online_url"].rstrip("/") + "/chat/completions",
                                     data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json",
                                              **({"Authorization": "Bearer " + cfg["online_key"]}
                                                 if cfg.get("online_key") else {})})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"]
    msgs = [dict(m) for m in messages]
    if pics:
        msgs[-1]["images"] = pics
    body = {"model": local_model(cfg), "messages": msgs, "stream": False,
            "options": {"temperature": temperature, "num_ctx": context}}
    if json_mode:
        body["format"] = "json"
    try:
        return _json(OLLAMA + "/api/chat", body, timeout=timeout)["message"]["content"]
    except urllib.error.HTTPError as e:
        if e.code != 500:
            raise
        threading.Event().wait(3)          # the runner restarted (often short of video memory): once more
        return _json(OLLAMA + "/api/chat", body, timeout=timeout)["message"]["content"]


def parse_json(text):
    """The first {...} in an AI answer, as a dict ({} when there isn't one)."""
    text = re.sub(r"(?s)<think>.*?</think>", "", text or "")
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return {}
    try:
        d = json.loads(m.group(0))
        return d if isinstance(d, dict) else {}
    except ValueError:
        return {}


# ---- speaking ---------------------------------------------------------------------------------
def has_japanese(text):
    return bool(re.search(r"[぀-ヿ㐀-鿿]", text or ""))


def speech_chunks(text, size=350):
    """[(start, end)] spans of the text, a sentence or a few at a time, for reading aloud
    piece by piece (so reading starts quickly and the piece being read can be highlighted)."""
    spans = []
    for m in re.finditer(r"[^\n.!?。！？]+[.!?。！？]*[\"')\]]*", text):
        s, e = m.start(), m.end()
        if not text[s:e].strip():
            continue
        if spans and e - spans[-1][0] <= size and "\n" not in text[spans[-1][1]:s]:
            spans[-1] = (spans[-1][0], e)
        else:
            spans.append((s, e))
    return [(s + len(text[s:e]) - len(text[s:e].lstrip()), e) for s, e in spans]


class Speaker:
    """Reads text aloud with Piper on this PC, one piece at a time: the next piece is being
    made while the current one plays. on_piece(start, end) says which piece is playing."""

    def __init__(self, cfg=None):
        self.name = (cfg or settings()).get("voice") or DEFAULT_VOICE
        self.dir = os.path.join(DATA, "voices")
        self.model = os.path.join(self.dir, self.name + ".onnx")
        self.stopping = threading.Event()
        self.player = None

    def ready(self):
        return os.path.isfile(self.model) and os.path.isfile(self.model + ".json")

    def download(self):
        lang, speaker, quality = self.name.split("-")
        url = f"{VOICE_BASE}/{lang.split('_')[0]}/{lang}/{speaker}/{quality}/{self.name}.onnx"
        os.makedirs(self.dir, exist_ok=True)
        for suffix in (".onnx.json", ".onnx"):
            tmp = self.model.replace(".onnx", suffix) + ".part"
            urllib.request.urlretrieve(url.replace(".onnx", suffix), tmp)
            os.replace(tmp, self.model.replace(".onnx", suffix))

    def _make(self, text, path):
        subprocess.run([sys.executable, "-m", "piper", "-m", self.model, "-f", path],
                       input=text, text=True, capture_output=True, timeout=300, check=True)

    def read(self, text, on_piece=None, done=None):
        """Read the text aloud in the background. done() when finished or stopped."""
        self.stop()
        self.stopping = stop = threading.Event()
        pieces = speech_chunks(text)
        made = queue.Queue(maxsize=2)
        tmp = tempfile.mkdtemp(prefix="kantanos-read-")

        def maker():
            for i, (s, e) in enumerate(pieces):
                if stop.is_set():
                    break
                path = os.path.join(tmp, f"{i}.wav")
                try:
                    self._make(text[s:e], path)
                except (OSError, subprocess.SubprocessError):
                    continue
                made.put((s, e, path))
            made.put(None)

        def player():
            try:
                while not stop.is_set():
                    item = made.get()
                    if item is None:
                        break
                    s, e, path = item
                    if on_piece:
                        on_piece(s, e)
                    self.player = subprocess.Popen(["pw-play", path], stdout=subprocess.DEVNULL,
                                                   stderr=subprocess.DEVNULL)
                    self.player.wait()
                    os.remove(path)
            finally:
                stop.set()
                while not made.empty():
                    made.get_nowait()
                subprocess.run(["rm", "-rf", tmp])
                if done:
                    done()
        threading.Thread(target=maker, daemon=True).start()
        threading.Thread(target=player, daemon=True).start()

    def stop(self):
        self.stopping.set()
        if self.player and self.player.poll() is None:
            self.player.terminate()


def self_test():
    assert speech_chunks("Hello there. How are you?\n\nFine!") == [(0, 25), (27, 32)], speech_chunks(
        "Hello there. How are you?\n\nFine!")
    assert has_japanese("お知らせ") and not has_japanese("Notice")
    assert parse_json('x <think>{"a":1}</think> {"b": 2} y') == {"b": 2}
    assert online_host({"provider": "online", "online_url": "https://openrouter.ai/api/v1"}) == "openrouter.ai"
    assert online_host({"provider": "local"}) == ""
    return True
