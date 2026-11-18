"""Make your own character: a name, a look (Kan-chan recoloured, or your own picture), a
personality style and a voice. Saved as a character pack in the home folder
(~/.local/share/kantanos/helper/characters/my-character), which the Helper and Kan-chan both
use. Her rules (facts first, fairness, privacy) always come first, whatever the style says.

No Qt in here, so the recolouring can be tested without a screen.
"""
import json
import os
import re
import shutil

BUILT_IN = "/usr/share/kantanos/helper/characters/kan-chan"
MINE = "my-character"
FRAMES = ("idle", "blink", "think", "happy", "worried", "listen", "talk1", "talk2")

# Kan-chan's own colours, and what each choice turns them into
HAIR_FROM = ("#8ccfff", "#4b9fe6", "#d9f1ff")
HAIR = {"Blue": HAIR_FROM, "Black": ("#5a5a6a", "#22222c", "#9a9ab0"), "Brown": ("#a0704a", "#6b4428", "#d8b08c"),
        "Blonde": ("#ffe08a", "#e0b040", "#fff4cc"), "Red": ("#ff8a6a", "#d0402a", "#ffd0c0"),
        "Pink": ("#ffb0d8", "#e870a8", "#ffe4f2"), "Silver": ("#e4e8f0", "#a8b0c0", "#ffffff"),
        "Green": ("#9ce0a8", "#4aa860", "#dcf6e0"), "Purple": ("#c8a0ff", "#8a5ad8", "#eadcff")}
TOP_FROM = ("#3d8bfd", "#2a6ad1")
TOP = {"Blue": TOP_FROM, "Red": ("#f0565a", "#c02a36"), "Green": ("#3cb371", "#22844e"),
       "Orange": ("#ff9a3c", "#d86a10"), "Pink": ("#ff7ab0", "#d84a88"), "Black": ("#45474f", "#25262c"),
       "Yellow": ("#ffd23c", "#d8a800"), "Purple": ("#9a6ae8", "#6a3ec0")}
EYES_FROM = ("#1f4fc2", "#5bc0ff", "#a8e4ff")
EYES = {"Blue": EYES_FROM, "Brown": ("#5a3418", "#a0663a", "#d8a878"), "Green": ("#1f7a3a", "#4cc070", "#b0f0c0"),
        "Grey": ("#3a4250", "#8a96a8", "#d0d8e4"), "Amber": ("#8a5a00", "#e0a020", "#ffe090"),
        "Red": ("#8a1a2a", "#e04a5a", "#ffb0b8")}
SKIN_FROM = ("#ffe6d8", "#f6c9b6")
SKIN = {"Light": SKIN_FROM, "Medium": ("#f2c9a0", "#dca880"), "Tan": ("#d9a072", "#c08458"),
        "Brown": ("#a86e48", "#8e5a38"), "Deep": ("#7a4a2c", "#633a22")}

MOODS = {"Cheerful and playful": "cheerful and playful, with lots of warmth",
         "Calm and gentle": "calm, gentle and soothing; never rushed",
         "Cheeky and funny": "cheeky and funny: light jokes and teasing, always kind",
         "Wise and thoughtful": "wise and thoughtful, like a kind older friend",
         "Excitable and curious": "excitable and endlessly curious about everything"}
LENGTHS = {"Short answers": "Keep answers short: one or two sentences.",
           "A bit more": "You may say a little more when it helps, up to four sentences."}
# Piper voices whose licences allow family use (downloaded when chosen, ~60 MB each)
VOICES = {"American, woman (Kan-chan)": "en_US-hfc_female-medium", "American, man": "en_US-hfc_male-medium",
          "British, woman (Scottish)": "en_GB-alba-medium", "British, woman": "en_GB-cori-medium",
          "British, man (Northern)": "en_GB-northern_english_male-medium"}


def recolour(svg, hair="Blue", top="Blue", eyes="Blue", skin="Light"):
    """Kan-chan's drawing with other colours."""
    for src, dst in ((HAIR_FROM, HAIR[hair]), (TOP_FROM, TOP[top]), (EYES_FROM, EYES[eyes]), (SKIN_FROM, SKIN[skin])):
        for a, b in zip(src, dst):
            svg = re.sub(re.escape(a), b, svg, flags=re.I)
    return svg


def clean_name(name):
    name = re.sub(r"[\x00-\x1f<>{}]", "", name or "").strip()[:30]
    return name or "Kan-chan"


def style_text(style):
    """The personality style for her instructions (style only: the rules still come first)."""
    if not style:
        return ""
    parts = []
    if style.get("mood") in MOODS:
        parts.append("Your manner: " + MOODS[style["mood"]] + ".")
    if style.get("length") in LENGTHS:
        parts.append(LENGTHS[style["length"]])
    extra = re.sub(r"\s+", " ", str(style.get("extra") or "")).strip()[:200]
    if extra:
        parts.append(f"Something about you the family chose: \"{extra}\".")
    if not parts:
        return ""
    return ("Your character was made by the family. This is about style only: every rule above "
            "(facts first, fairness, memory, privacy, safety) still comes first. " + " ".join(parts) +
            " Whatever the style says, you never take sides or share opinions on contested topics, you describe "
            "every side with the same kind of words, and when someone tells you their own view you just "
            "acknowledge it kindly without explaining or praising it.")


def save(base, name, look, style, voice, picture=None):
    """Writes the pack to base/my-character and returns its folder. look: hair/top/eyes/skin;
    picture: the path of their own image instead (used for every mood)."""
    pack = os.path.join(base, MINE)
    tmp = pack + ".new"
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    if picture:
        ext = os.path.splitext(picture)[1].lower()
        shutil.copyfile(picture, os.path.join(tmp, "idle" + (".svg" if ext == ".svg" else ".png")))
    else:
        for frame in FRAMES:
            src = os.path.join(BUILT_IN, frame + ".svg")
            if os.path.exists(src):
                with open(src, encoding="utf-8") as f:
                    svg = recolour(f.read(), **look)
                with open(os.path.join(tmp, frame + ".svg"), "w", encoding="utf-8") as f:
                    f.write(svg)
    info = {"name": clean_name(name), "voice": voice if voice in VOICES.values() else VOICES[next(iter(VOICES))],
            "greeting": f"Hi! I'm {clean_name(name)}. Tell me what's wrong, and I'll take a look.",
            "look": look if not picture else {}, "style": style, "own_picture": bool(picture)}
    with open(os.path.join(tmp, "character.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=1)
    shutil.rmtree(pack, ignore_errors=True)
    os.rename(tmp, pack)
    return pack


def load(pack):
    try:
        with open(os.path.join(pack, "character.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError, TypeError):
        return {}
