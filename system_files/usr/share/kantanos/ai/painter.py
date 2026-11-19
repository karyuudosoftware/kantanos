"""Making and fixing pictures on this PC, for the Picture helper (kantan-pictures).

Engine: stable-diffusion.cpp (MIT, ships in the image at /usr/lib/kantanos/sd, Vulkan: NVIDIA,
AMD and Intel graphics). Model: FLUX.2 [klein] 4B (Apache-2.0) with its Qwen3 4B text encoder
and the FLUX.2 small decoder (both Apache-2.0); one model both makes pictures from words and
changes photos from plain instructions. The models download once (about 7.3 GB, checked
against the checksums below) into ~/.local/share/kantanos/pictures/models. Nothing is sent
anywhere: the words and the photos stay on this PC.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import urllib.request

ENGINE = os.environ.get("KANTAN_SD", "/usr/libexec/kantanos/sd-cli")
MODELS = os.path.join(os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")), "kantanos", "pictures",
                      "models")
HF = "https://huggingface.co"
FILES = {   # role: (file, url, size, sha256)
    "diffusion": ("flux-2-klein-4b-Q8_0.gguf",
                  HF + "/leejet/FLUX.2-klein-4B-GGUF/resolve/3b1f5a9dc3abb32238b053aeb3d823c30afdacbd/flux-2-klein-4b-Q8_0.gguf",
                  4300629440, "0bba6951258ec8f92d51114a8fa13e66828297bfff58a738f52729b3ef66fa28"),
    "llm": ("Qwen3-4B-Q6_K.gguf", HF + "/unsloth/Qwen3-4B-GGUF/resolve/main/Qwen3-4B-Q6_K.gguf",
            3306261792, "002b8b61c298976afc2c9c3ca65f9dbb28deba22c4b6381853dfaa92b5690022"),
    "vae": ("full_encoder_small_decoder.safetensors",
            HF + "/black-forest-labs/FLUX.2-small-decoder/resolve/main/full_encoder_small_decoder.safetensors",
            249519092, "ea4273f02d1fafbf8e1d1c2cf6018ed8748652eb0bf34f2dd91171f16f15ab62"),
}
TOTAL_GB = round(sum(f[2] for f in FILES.values()) / 1e9, 1)
SIZES = {"square": (1024, 1024), "wide": (1344, 768), "tall": (768, 1344)}
STYLES = {"": "", "photo": "a realistic photograph, natural light", "watercolour": "a soft watercolour painting",
          "cartoon": "a bright, friendly cartoon illustration", "oil": "an oil painting with visible brush strokes",
          "pencil": "a pencil sketch", "3d": "a cute 3D render", "anime": "an anime-style illustration",
          "storybook": "a children's storybook illustration"}
FIXES = {
    "tidy": "Restore this old photograph: remove the scratches, dust, spots, creases and tears, bring back the "
            "faded contrast, and sharpen it gently. If it is a black-and-white or sepia photo, keep it black and "
            "white or sepia. Keep every person, face, pose and object exactly as it is.",
    "colour": "Colourise this black-and-white photograph with natural, realistic colours. Keep everything else "
              "exactly the same.",
    "remove": "Remove {what} from the picture and fill the space naturally with the background around it. Keep "
              "everything else exactly the same.",
}


# ---- family-friendly words only ----------------------------------------------------------------
BLOCKED = re.compile(r"\b(nude|nudes|naked|nsfw|porn\w*|sex\w*|topless|lingerie|erotic\w*|hentai|gore|gory|"
                     r"beheaded|dismember\w*|bloody corpse)\b|ヌード|裸|エロ|ポルノ|セックス|全裸", re.I)


def family_friendly(text):
    return not BLOCKED.search(text or "")


# ---- the models --------------------------------------------------------------------------------
def model_path(role):
    return os.path.join(MODELS, FILES[role][0])


def models_ready():
    return all(os.path.isfile(model_path(r)) and os.path.getsize(model_path(r)) == FILES[r][2] for r in FILES)


def engine_ready():
    return os.access(ENGINE, os.X_OK)


def free_disk_gb(path=None):
    p = path or MODELS
    while not os.path.isdir(p):
        p = os.path.dirname(p) or "/"
    return shutil.disk_usage(p).free / 1e9


def download(progress=None, stop=None):
    """Fetch the models (resuming a broken download), each checked against its checksum."""
    os.makedirs(MODELS, exist_ok=True)
    done_before = sum(os.path.getsize(model_path(r)) for r in FILES
                      if os.path.isfile(model_path(r)) and os.path.getsize(model_path(r)) == FILES[r][2])
    total = sum(f[2] for f in FILES.values())
    got = done_before
    for role, (name, url, size, sha) in FILES.items():
        dest = model_path(role)
        if os.path.isfile(dest) and os.path.getsize(dest) == size:
            continue
        part = dest + ".part"
        have = os.path.getsize(part) if os.path.exists(part) else 0
        req = urllib.request.Request(url, headers={"User-Agent": "KantanOS-Pictures/1.0",
                                                   **({"Range": f"bytes={have}-"} if have else {})})
        with urllib.request.urlopen(req, timeout=60) as r, open(part, "ab" if have else "wb") as f:
            if have and r.status != 206:          # the server started again from the beginning
                f.truncate(0)
                have = 0
            got += have
            while True:
                if stop is not None and stop.is_set():
                    raise InterruptedError("stopped")
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
                got += len(chunk)
                if progress:
                    progress(got, total)
        h = hashlib.sha256()
        with open(part, "rb") as f:
            for block in iter(lambda: f.read(1 << 22), b""):
                h.update(block)
        if h.hexdigest() != sha:
            os.remove(part)
            raise ValueError(f"{name} didn't download correctly (it doesn't match its checksum). Try again.")
        os.replace(part, dest)


# ---- sharing the graphics card with the chat AI ----------------------------------------------
def free_video_memory(ollama="http://127.0.0.1:11434"):
    """Ask Ollama to unload its models for now (they load again the next time they're asked),
    so pictures get the graphics card's memory."""
    try:
        with urllib.request.urlopen(ollama + "/api/ps", timeout=3) as r:
            loaded = [m["name"] for m in json.load(r).get("models", [])]
        for name in loaded:
            req = urllib.request.Request(ollama + "/api/generate", data=json.dumps(
                {"model": name, "keep_alive": 0}).encode(), headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=30).read()
    except (OSError, ValueError, KeyError):
        pass


def video_memory_mb():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=10).stdout
        if out.strip():
            return max(int(x) for x in out.split())
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    import glob
    best = 0
    for p in glob.glob("/sys/class/drm/card*/device/mem_info_vram_total"):
        try:
            best = max(best, int(open(p).read()) // (1 << 20))
        except (OSError, ValueError):
            pass
    return best


# ---- running the engine ------------------------------------------------------------------------
STEP_RE = re.compile(r"\|\s*(\d+)/(\d+)\s*-")


def edit_size(w, h, longest=1024):
    """The output size for a photo being changed: same shape, longest side 1024, multiples of 16."""
    k = longest / max(w, h)
    return max(256, int(w * k) // 16 * 16), max(256, int(h * k) // 16 * 16)


def command(prompt, out, size=(1024, 1024), seed=-1, reference=None, steps=4, low_memory=None, cpu=False):
    w, h = size
    cmd = [ENGINE, "--diffusion-model", model_path("diffusion"), "--llm", model_path("llm"),
           "--vae", model_path("vae"), "-p", prompt, "--cfg-scale", "1.0", "--steps", str(steps),
           "--sampling-method", "euler", "-W", str(w), "-H", str(h), "--seed", str(seed), "-o", out]
    if reference:
        cmd += ["-r", reference]
    if low_memory is None:
        low_memory = video_memory_mb() < 12000
    if low_memory:
        cmd.append("--offload-to-cpu")
    if cpu:
        cmd += ["--backend", "cpu"]
    return cmd


def run(cmd, progress=None, stop=None, timeout=3600):
    """Run the engine; progress(step, steps) while it draws. Returns the output file."""
    out = cmd[cmd.index("-o") + 1]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    tail, buf, t0 = [], b"", time.time()
    while True:
        chunk = p.stdout.read1(4096) if hasattr(p.stdout, "read1") else p.stdout.read(4096)
        if not chunk:
            break
        buf += chunk
        *lines, buf = re.split(rb"[\r\n]", buf)
        for raw in lines:
            line = raw.decode("utf-8", "replace")
            if line.strip():
                tail = (tail + [line.strip()])[-12:]
            m = STEP_RE.search(line)
            if m and progress:
                progress(int(m.group(1)), int(m.group(2)))
        if stop is not None and stop.is_set():
            p.terminate()
            raise InterruptedError("stopped")
        if time.time() - t0 > timeout:
            p.kill()
            raise TimeoutError("it took too long")
    code = p.wait()
    if code != 0 or not os.path.isfile(out):
        why = next((l for l in reversed(tail) if "error" in l.lower() or "fail" in l.lower()), tail[-1] if tail else "")
        if "out of memory" in why.lower() or "ErrorOutOfDeviceMemory" in why:
            why = "the graphics card ran out of memory; close games or other AI programs and try again"
        raise RuntimeError(why or f"the picture engine stopped (code {code})")
    return out


def picture_name(folder, words, ext=".png"):
    base = re.sub(r"\s+", " ", re.sub(r"[^\w\- ()]+", " ", words, flags=re.U)).strip()[:50] or "Picture"
    p, n = os.path.join(folder, base + ext), 2
    while os.path.exists(p):
        p, n = os.path.join(folder, f"{base} ({n}){ext}"), n + 1
    return p


def mark_made_with_ai(path, words):
    """Write 'Made with AI' and the words into the picture's own description, so anyone who gets
    it can tell (shown in Gwenview's and Dolphin's information panels)."""
    try:
        from PySide6.QtGui import QImage
        img = QImage(path)
        if not img.isNull():
            img.setText("Description", f"Made with AI on KantanOS (FLUX.2 klein): {words}")
            img.setText("Software", "KantanOS Picture helper")
            img.save(path)
    except ImportError:
        pass


def self_test():
    assert family_friendly("a cat in a spacesuit, watercolour") and not family_friendly("a naked man")
    assert not family_friendly("裸の人") and family_friendly("Sussex countryside in spring")
    assert edit_size(4000, 3000) == (1024, 768) and edit_size(800, 1200) == (672, 1024)
    c = command("a cat", "/tmp/x.png", (1344, 768), 7, reference="/tmp/r.jpg", low_memory=True)
    assert c[c.index("-W") + 1] == "1344" and "-r" in c and "--offload-to-cpu" in c and c[c.index("--seed") + 1] == "7"
    assert STEP_RE.search("  |=========>      | 2/4 - 1.23s/it").groups() == ("2", "4")
    with tempfile.TemporaryDirectory() as tmp:
        open(os.path.join(tmp, "A cat.png"), "w").close()
        assert picture_name(tmp, "A cat!").endswith("A cat (2).png")
        assert picture_name(tmp, "old (fixed)").endswith("old (fixed).png")
    assert TOTAL_GB == 7.9, TOTAL_GB
    return True
