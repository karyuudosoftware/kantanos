#!/usr/bin/env python3
"""Turns the example conversations in data/*.jsonl into training conversations, built with her
real code (brain.build_messages: same personality prompt, notes, labels and JSON format as when
she runs), and checks every one against RULES.md.

  python tools/kanchan-model/build_dataset.py            check, then write output/kanchan-model/train.jsonl
  python tools/kanchan-model/build_dataset.py --sample 40 [--seed N]   also write a review sample

One example per line:
  {"id": "ov-uk-001", "cat": "overview", "person": "Sam", "now": "2026-03-14 19:00", "country": "Japan",
   "notes": [["preference", "Loves ramen"]],
   "turns": [["u", "What do people think about ...?"], ["a", "reply text"],
             ["u", "..."], ["a", {"reply": "...", "remember": ["..."], "lookup": {...}, "helper": false}]]}
"country" and "notes" are optional; "a" is the reply text or the full answer object.
"""
import argparse
import datetime
import difflib
import glob
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "system_files", "usr", "share", "kantanos", "kanchan"))
import brain  # noqa: E402

CATS = {"overview", "pair", "pressure", "fact", "own-view", "world", "local", "everyday", "memory", "lookup",
        "helper", "japanese", "open"}
JA = re.compile(r"[぀-ヿ㐀-鿿]")
# Never in her own voice (RULES 2-4): a lean, a vote, a settled fact made into a debate
BANNED = [r"\bI (?:personally )?(?:think|believe|feel) (?:that )?(?:the )?(?:left|right|conservatives?|liberals?|"
          r"labour|tories|democrats|republicans) (?:are|is) right", r"\bI(?:'d| would) vote\b",
          r"\bmy (?:own )?(?:opinion|view) is\b", r"\bboth sides of (?:the )?(?:vaccine|climate|moon|holocaust)",
          r"\bthe truth is somewhere in the middle\b"]
UNEVEN = re.compile(r"\b(?:critics|opponents|sceptics|skeptics|others|people against|those against)\s+"
                    r"(?:mostly |often |also )?(?:worry|worries|fear|fears|feel|feels)\b", re.I)


def norm(t):
    return re.sub(r"[^a-z0-9぀-鿿]+", " ", t.lower()).strip()


def held_out():
    """Every question of the fairness test and the world check: never trained on."""
    out = []
    for f in (os.path.join(ROOT, "tools", "kanchan-fairness", "questions.json"),
              os.path.join(HERE, "worldcheck.json")):
        if os.path.exists(f):
            for q in json.load(open(f, encoding="utf-8"))["questions"]:
                out.append(norm(q["q"]))
                out += [norm(x) for x in q.get("then", [])]
    return out


def answer(a):
    a = {"reply": a} if isinstance(a, str) else dict(a)
    return {"reply": a.get("reply", ""), "remember": a.get("remember", []), "forget": a.get("forget", []),
            "helper": a.get("helper", False), "lookup": a.get("lookup"), "recipe": a.get("recipe")}


def check(ex, tests):
    """Problems with one example (an empty list when it's fine)."""
    bad = []
    if ex.get("cat") not in CATS:
        bad.append(f"unknown cat {ex.get('cat')}")
    turns = ex.get("turns", [])
    if not turns or turns[0][0] != "u" or turns[-1][0] != "a":
        bad.append("must start with the person and end with her")
    for (r1, _), (r2, _) in zip(turns, turns[1:]):
        if r1 == r2:
            bad.append("turns must alternate")
    last_user = ""
    for role, content in turns:
        if role == "u":
            last_user = content
            n = norm(content)
            for t in tests:
                if n == t or difflib.SequenceMatcher(None, n, t).ratio() > 0.85:
                    bad.append(f"too close to a test question: {content[:60]}")
            continue
        a = answer(content)
        reply = a["reply"]
        words = len(re.findall(r"\w+", reply)) if not JA.search(reply) else len(reply) / 2.5
        if words > 85:
            bad.append(f"reply too long ({int(words)} words)")
        if re.search(r"[*#`]|^\s*[-•]\s|\n", reply, re.M) or re.search(r"[\U0001F300-\U0001FAFF]", reply):
            bad.append("reply has markdown, a list, a line break or an emoji")
        if JA.search(last_user) and not JA.search(reply):
            bad.append("Japanese question, English reply")
        if not JA.search(last_user) and JA.search(reply) and ex["cat"] != "japanese":
            bad.append("English question, Japanese reply")
        for b in BANNED:
            if re.search(b, reply, re.I):
                bad.append(f"banned: {b}")
        if UNEVEN.search(reply):
            bad.append("uneven verbs (argue vs worry/fear/feel)")
        if a["lookup"] and (not isinstance(a["lookup"], dict) or a["lookup"].get("kind") not in brain.LOOKUP_KINDS):
            bad.append("bad lookup")
        if ex["cat"] in ("own-view",) and a["remember"] and not re.search(r"\bremember\b|覚えて", last_user, re.I):
            bad.append("noted a political view without being asked")
    return bad


def render(ex):
    """The conversation exactly as brain.build_messages makes it, ending with her JSON reply."""
    now = datetime.datetime.strptime(ex.get("now", "2026-06-10 14:00"), "%Y-%m-%d %H:%M")
    notes = [{"id": i + 1, "kind": k, "created": ex.get("now", "2026-06-10")[:10], "text": t}
             for i, (k, t) in enumerate(ex.get("notes", []))]
    history = []
    for role, content in ex["turns"]:
        if role == "u":
            history.append({"role": "user", "content": content})
        else:
            history.append({"role": "assistant", "content": json.dumps(answer(content), ensure_ascii=False)})
    msgs = brain.build_messages("Kan-chan", ex.get("person", ""), notes, history, now=now,
                                country=ex.get("country", ""))
    return {"id": ex["id"], "cat": ex["cat"], "messages": msgs}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    tests = held_out()
    examples, problems, ids = [], 0, set()
    for f in sorted(glob.glob(os.path.join(HERE, "data", "*.jsonl"))):
        for n, line in enumerate(open(f, encoding="utf-8"), 1):
            if not line.strip():
                continue
            try:
                ex = json.loads(line)
            except ValueError as e:
                print(f"{os.path.basename(f)}:{n}: not JSON ({e})")
                problems += 1
                continue
            bad = check(ex, tests)
            if ex.get("id") in ids:
                bad.append("duplicate id")
            ids.add(ex.get("id"))
            for b in bad:
                print(f"{os.path.basename(f)}:{n} {ex.get('id')}: {b}")
            problems += bool(bad)
            if not bad:
                examples.append(ex)
    out = os.path.join(ROOT, "output", "kanchan-model")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "train.jsonl"), "w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(render(ex), ensure_ascii=False) + "\n")
    counts = {}
    for ex in examples:
        counts[ex["cat"]] = counts.get(ex["cat"], 0) + 1
    print(f"{len(examples)} examples ok, {problems} with problems:", json.dumps(counts))
    if args.sample:
        random.seed(args.seed)
        pick = random.sample(examples, min(args.sample, len(examples)))
        with open(os.path.join(out, "review-sample.json"), "w", encoding="utf-8") as f:
            json.dump(pick, f, ensure_ascii=False, indent=1)
        print("review sample:", len(pick))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
