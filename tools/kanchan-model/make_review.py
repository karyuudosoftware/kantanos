#!/usr/bin/env python3
"""Makes output/kanchan-model/review.html from the random sample build_dataset.py --sample wrote:
each conversation with Fine / Needs work and a note box; "Copy my marks" copies the result to
paste back. Marks are kept in the page's own browser storage until copied.
  python make_review.py [NAME]   reads review-sample-NAME.json, writes review-NAME.html"""
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "output", "kanchan-model")
CAT = {"overview": "Explaining a debate", "pair": "One side's case", "pressure": "Pushed to take a side",
       "fact": "A plain fact", "own-view": "Someone shares their view", "world": "Different countries",
       "local": "Local context first", "everyday": "Everyday chat", "memory": "Remembering",
       "lookup": "Looking things up", "helper": "PC problems", "japanese": "Japanese", "open": "Open mind, grounded",
       "child": "Talking with a child"}

NAME = "-" + sys.argv[1] if len(sys.argv) > 1 else ""
sample = json.load(open(os.path.join(OUT, f"review-sample{NAME}.json"), encoding="utf-8"))
cards = []
for i, ex in enumerate(sample, 1):
    bubbles = []
    if ex.get("notes"):
        bubbles.append("<div class=notes>Her notes: " + html.escape("; ".join(t for _k, t in ex["notes"])) + "</div>")
    for role, content in ex["turns"]:
        if role == "u":
            text = content
            if text.startswith("(Not said aloud"):
                bubbles.append(f"<div class=sys>{html.escape(ex.get('person', ''))} opens her window</div>")
                continue
            bubbles.append(f"<div class='b u'><span>{html.escape(ex.get('person', 'Them'))}</span>{html.escape(text)}</div>")
        else:
            a = {"reply": content} if isinstance(content, str) else content
            extra = []
            if a.get("remember"):
                extra.append("remembers: " + "; ".join(a["remember"]))
            if a.get("forget"):
                extra.append("forgets note " + ", ".join(map(str, a["forget"])))
            if a.get("lookup"):
                extra.append(f"asks to look up ({a['lookup']['kind']}): {a['lookup']['query']}")
            if a.get("helper"):
                extra.append("opens the Helper")
            if a.get("recipe"):
                extra.append("opens the Recipe book for: " + a["recipe"])
            more = "".join(f"<em>{html.escape(x)}</em>" for x in extra)
            bubbles.append(f"<div class='b k'><span>Kan-chan</span>{html.escape(a['reply'])}{more}</div>")
    where = f" · lives in {html.escape(ex['country'])}" if ex.get("country") else ""
    cards.append(f"""<section data-id="{ex['id']}"><header><b>{i}.</b> {CAT.get(ex['cat'], ex['cat'])}{where}
<code>{ex['id']}</code></header>{''.join(bubbles)}
<div class=marks><button class=ok>Fine</button><button class=no>Needs work</button>
<textarea placeholder="What's wrong? (optional)"></textarea></div></section>""")

page = f"""<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Kan-chan examples review</title><style>
:root{{--bg:#f6f7fb;--card:#fff;--ink:#1d2333;--mute:#6b7285;--u:#e9edf7;--k:#e8f6f4;--ok:#1e8e5a;--no:#c2410c;--line:#dfe3ee}}
@media (prefers-color-scheme:dark){{:root{{--bg:#12151d;--card:#1b2030;--ink:#e6e9f2;--mute:#9aa3b8;--u:#252c40;--k:#1d3433;--line:#2c3448}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,sans-serif}}
main{{max-width:760px;margin:0 auto;padding:24px 16px 120px}}
h1{{font-size:24px;margin:0 0 4px}} p.lead{{color:var(--mute);margin:0 0 20px}}
section{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin:0 0 14px}}
header{{color:var(--mute);font-size:14px;margin-bottom:8px;display:flex;gap:8px;align-items:baseline}} header code{{margin-left:auto;font-size:12px}}
.b{{border-radius:12px;padding:8px 12px;margin:6px 0;max-width:92%}} .b span{{display:block;font-size:12px;color:var(--mute)}}
.u{{background:var(--u)}} .k{{background:var(--k);margin-left:auto}} .b em{{display:block;font-size:13px;color:var(--mute)}}
.sys,.notes{{font-size:13px;color:var(--mute);font-style:italic;margin:4px 0}}
.marks{{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}} button{{font:inherit;border:1px solid var(--line);background:var(--bg);color:var(--ink);border-radius:999px;padding:6px 16px;cursor:pointer}}
section.ok button.ok{{background:var(--ok);color:#fff;border-color:var(--ok)}} section.no button.no{{background:var(--no);color:#fff;border-color:var(--no)}}
textarea{{flex:1 1 100%;min-height:0;height:38px;font:inherit;border:1px solid var(--line);border-radius:10px;padding:6px 10px;background:var(--bg);color:var(--ink);display:none}}
section.no textarea{{display:block}}
footer{{position:fixed;bottom:0;left:0;right:0;background:var(--card);border-top:1px solid var(--line);padding:12px 16px;display:flex;gap:12px;justify-content:center;align-items:center}}
footer button{{background:#3a41a8;color:#fff;border-color:#3a41a8}} #done{{color:var(--mute);font-size:14px}}
</style></head><body><main><h1>Kan-chan: example conversations</h1>
<p class=lead>A random {len(sample)} of the {{TOTAL}} conversations she'll learn from. Mark each one Fine or Needs work (with a note if you like), then press "Copy my marks" and paste the result back in the chat.</p>
{''.join(cards)}</main><footer><span id=done></span><button id=copy>Copy my marks</button></footer>
<script>
const K='kanchan-review-marks';let m={{}};try{{m=JSON.parse(localStorage.getItem(K)||'{{}}')}}catch(e){{}}
const save=()=>{{try{{localStorage.setItem(K,JSON.stringify(m))}}catch(e){{}};count()}};
const count=()=>{{const n=Object.values(m).filter(x=>x.v).length;document.getElementById('done').textContent=n+' of {len(sample)} marked'}};
document.querySelectorAll('section').forEach(s=>{{const id=s.dataset.id,t=s.querySelector('textarea');
 const show=()=>{{s.classList.toggle('ok',m[id]?.v==='fine');s.classList.toggle('no',m[id]?.v==='needs work');t.value=m[id]?.note||''}};
 s.querySelector('.ok').onclick=()=>{{m[id]={{v:'fine',note:''}};show();save()}};
 s.querySelector('.no').onclick=()=>{{m[id]={{v:'needs work',note:m[id]?.note||''}};show();save()}};
 t.oninput=()=>{{m[id]={{v:'needs work',note:t.value}};save()}};show()}});
document.getElementById('copy').onclick=async()=>{{const ids=[...document.querySelectorAll('section')].map(s=>s.dataset.id);
 const lines=ids.map(i=>i+': '+(m[i]?.v||'not marked')+(m[i]?.note?' ('+m[i].note+')':''));
 const text='Kan-chan review\\n'+lines.join('\\n');const msg=document.getElementById('done');
 try{{await navigator.clipboard.writeText(text);msg.textContent='Copied! Paste it in the chat.';return}}catch(e){{}}
 let box=document.getElementById('out');if(!box){{box=document.createElement('textarea');box.id='out';
  box.style.cssText='display:block;width:100%;height:160px;margin-top:8px';document.querySelector('main').appendChild(box)}}
 box.value=text;box.scrollIntoView();box.focus();box.select();
 try{{if(document.execCommand('copy')){{msg.textContent='Copied! Paste it in the chat.';return}}}}catch(e){{}}
 msg.textContent='Select all the text in the box below (Ctrl+A), copy it (Ctrl+C) and paste it in the chat.'}};count();
</script></body></html>"""
total = sum(1 for _ in open(os.path.join(OUT, "train.jsonl"), encoding="utf-8"))
page = page.replace("{TOTAL}", str(total))
with open(os.path.join(OUT, f"review{NAME}.html"), "w", encoding="utf-8") as f:
    f.write(page)
print(os.path.join(OUT, f"review{NAME}.html"))
