#!/usr/bin/env python3
"""Writes data/lookups.jsonl: examples of Kan-chan asking to look things up for anything that
changes over time (dates of coming events, who holds a job now, prices, scores, news, opening
times, weather), and of answering from the results turn exactly as brain.lookup_turn makes it.
The first trained model had only 8 such examples and stopped looking things up, answering
from stale memory instead. Run: python make_lookups.py (then build_dataset.py)."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "system_files", "usr", "share", "kantanos", "kanchan"))
import brain  # noqa: E402

ASK = ["Let me check that online for you.", "I'll look that up so I get it right.",
       "That changes, so let me check online.", "Let me look that up for you.",
       "I'd better check that online rather than guess.", "Good question, let me check the latest."]
ASK_JA = ["ちょっと調べてみるね。", "最新の情報を確認してみるね。", "ネットで確認してみるね。"]

# (id, person, now, question, kind, query, notes, country)
ASKS = [
    ("lk-001", "Gareth", "2026-05-03 18:20", "When's the next general election here?", "web", "next UK general election date", [], "the United Kingdom"),
    ("lk-002", "Priya", "2026-09-12 09:10", "Who's the Prime Minister of Canada at the moment?", "web", "current Prime Minister of Canada", [], ""),
    ("lk-003", "Tom", "2026-04-21 12:00", "When do the clocks go back this year?", "web", "UK clocks go back 2026 date", [], "the United Kingdom"),
    ("lk-004", "Ellie", "2026-02-02 17:45", "How much is a first class stamp now?", "web", "Royal Mail first class stamp price", [], "the United Kingdom"),
    ("lk-005", "Marcus", "2026-08-30 21:05", "What was the score in the Arsenal game tonight?", "web", "Arsenal result 30 August 2026", [], ""),
    ("lk-006", "Nadia", "2026-06-15 10:30", "What's the pound worth in euros today?", "web", "GBP to EUR exchange rate today", [], ""),
    ("lk-007", "Rhys", "2026-03-01 08:15", "Are there any train strikes this week?", "web", "UK rail strikes this week", [], "the United Kingdom"),
    ("lk-008", "Isla", "2026-11-03 16:40", "When does the next Pixar film come out?", "web", "next Pixar film release date", [], ""),
    ("lk-009", "Harry", "2026-07-19 14:00", "Who won the Tour de France?", "web", "Tour de France 2026 winner", [], ""),
    ("lk-010", "Mia", "2026-12-05 11:20", "Is the Natural History Museum in London open on Mondays?", "web", "Natural History Museum London opening hours", [], ""),
    ("lk-011", "Leo", "2026-10-11 19:30", "Who's the current world chess champion?", "web", "current world chess champion", [], ""),
    ("lk-012", "Ruby", "2026-01-20 13:15", "Where are the next Winter Olympics being held, and when?", "web", "next Winter Olympics host and dates", [], ""),
    ("lk-013", "Ade", "2026-05-27 09:00", "Has the Bank of England changed interest rates?", "web", "Bank of England interest rate latest", [], "the United Kingdom"),
    ("lk-014", "Jess", "2026-04-04 15:50", "What's petrol costing these days?", "web", "UK average petrol price this week", [], "the United Kingdom"),
    ("lk-015", "Callum", "2026-09-28 20:10", "Is there any news about the storm that's meant to be coming?", "web", "UK storm warning latest", [], "the United Kingdom"),
    ("lk-016", "Freya", "2026-06-01 07:50", "Is it going to be hot this weekend?", "weather", "Norwich", [["fact", "Freya lives in Norwich"]], ""),
    ("lk-017", "Arjun", "2026-02-18 12:30", "How old is the King now?", "facts", "Charles III", [], ""),
    ("lk-018", "Hannah", "2026-03-22 18:00", "Is the Eurovision final on this Saturday?", "web", "Eurovision 2026 final date", [], ""),
    ("lk-019", "Zoe", "2026-08-08 10:10", "When does the new series of Doctor Who start?", "web", "Doctor Who new series start date", [], ""),
    ("lk-020", "Ben", "2026-10-02 22:15", "What's the latest on the French elections?", "web", "France election latest results", [], ""),
    ("lk-021", "Grace", "2026-11-14 09:40", "How many people live in the world now?", "web", "world population 2026", [], ""),
    ("lk-022", "Liam", "2026-05-09 16:00", "What's the newest version of Windows?", "web", "latest Windows version", [], ""),
    ("lk-023", "Sophie", "2026-07-07 08:30", "Has the new iPhone come out yet?", "web", "latest iPhone release date", [], ""),
    ("lk-024", "Dan", "2026-12-20 12:00", "What time does the big supermarket shut on Christmas Eve?", "web", "Tesco Christmas Eve 2026 closing time", [], "the United Kingdom"),
    ("lk-025", "Kate", "2026-01-05 19:00", "Who's in the final of the darts?", "web", "World Darts Championship 2026 final", [], ""),
    ("lk-026", "Sam", "2026-06-22 07:15", "Do I need a coat today?", "weather", "Bristol", [["fact", "Sam lives in Bristol"]], ""),
    ("lk-027", "Chris", "2026-04-15 11:45", "How much does it cost to renew a passport now?", "web", "UK passport renewal fee", [], "the United Kingdom"),
    ("lk-028", "Amy", "2026-03-09 20:20", "When's the next full moon?", "web", "next full moon date", [], ""),
    ("lk-029", "Josh", "2026-09-03 18:30", "Who's the president of the United States right now?", "web", "current President of the United States", [], ""),
    ("lk-030", "Lily", "2026-10-25 15:00", "When's the next bank holiday?", "web", "next UK bank holiday", [], "the United Kingdom"),
]
ASKS_JA = [
    ("lk-j01", "ユキ", "2026-06-09 08:00", "次の衆議院選挙はいつ？", "web", "次の衆議院選挙 日程", [], "Japan"),
    ("lk-j02", "タロウ", "2026-04-02 12:10", "今の日本の総理大臣は誰？", "web", "現在の内閣総理大臣", [], "Japan"),
    ("lk-j03", "ミキ", "2026-03-18 18:45", "桜の開花はもう始まった？", "web", "桜 開花状況 東京", [["fact", "ミキさんは東京に住んでいる"]], "Japan"),
    ("lk-j04", "ケン", "2026-10-06 21:00", "今日のドジャースの試合、どうなった？", "web", "ドジャース 試合結果 10月6日", [], "Japan"),
    ("lk-j05", "アヤ", "2026-07-15 07:20", "明日は暑くなる？", "weather", "大阪", [["fact", "アヤさんは大阪に住んでいる"]], "Japan"),
]

# Two-step: question, her ask, the results turn (built by brain.lookup_turn), her answer from it.
ANSWERS = [
    ("la-001", "Gareth", "2026-05-03 18:25", "the United Kingdom", "When's the next general election here?", "web", "next UK general election date",
     {"source": "Wikipedia (Next United Kingdom general election)", "text": "The next United Kingdom general election must be held no later than 15 August 2029, under the Dissolution and Calling of Parliament Act 2022. The Prime Minister may call it earlier."},
     "According to Wikipedia, it has to be held by 15 August 2029 at the latest, though the Prime Minister can call it earlier than that."),
    ("la-002", "Marcus", "2026-08-30 21:10", "", "What was the score in the Arsenal game tonight?", "web", "Arsenal result 30 August 2026",
     {"source": "DuckDuckGo", "text": "Arsenal 2-1 Brighton (30 Aug 2026). Goals: Saka 23', Havertz 78'; Mitoma 55'."},
     "Arsenal won 2-1 against Brighton, according to DuckDuckGo. Saka and Havertz scored, and Mitoma got one back for Brighton."),
    ("la-003", "Freya", "2026-06-01 07:55", "", "Is it going to be hot this weekend?", "weather", "Norwich",
     {"source": "Open-Meteo", "text": "Weather for Norwich, England, United Kingdom. Now: partly cloudy, 14.2°C, wind 11 km/h.\nToday, Monday 1 June: partly cloudy; low 9.8°C, high 19.4°C; chance of rain 10%.\nTomorrow, Tuesday 2 June: light rain; low 11.0°C, high 17.1°C; chance of rain 70%.\nWednesday 3 June: overcast; low 10.2°C, high 16.5°C; chance of rain 35%."},
     "The forecast from Open-Meteo only goes to Wednesday so far, so I can't see the weekend yet. Today looks the warmest at about 19°C. Ask me again nearer the time and I'll check."),
    ("la-004", "Josh", "2026-09-03 18:35", "", "Who's the president of the United States right now?", "facts", "President of the United States",
     None, "I couldn't find anything useful online just now, sorry. You could try searching for it in the web browser."),
    ("la-005", "Ellie", "2026-02-02 17:50", "the United Kingdom", "How much is a first class stamp now?", "web", "Royal Mail first class stamp price",
     {"source": "DuckDuckGo", "text": "Royal Mail stamp prices: First Class £1.70, Second Class 87p (from April 2025). Large letter first class £2.60."},
     "DuckDuckGo says a first class stamp is £1.70, and second class is 87p. Those prices are from April 2025, so they may have gone up since."),
    ("la-006", "Ruby", "2026-01-20 13:20", "", "Where are the next Winter Olympics being held, and when?", "facts", "2030 Winter Olympics",
     {"source": "Wikipedia (2030 Winter Olympics)", "text": "The 2030 Winter Olympics will be held in the French Alps, with events in Auvergne-Rhône-Alpes and Provence-Alpes-Côte d'Azur, France. They are scheduled for February 2030."},
     "Wikipedia says the 2030 Winter Olympics will be in the French Alps, planned for February 2030. Mind you, the 2026 ones in Italy are only weeks away, if you meant those!"),
    ("la-007", "Hannah", "2026-03-22 18:05", "", "Is the Eurovision final on this Saturday?", "web", "Eurovision 2026 final date",
     {"source": "DuckDuckGo", "text": "Eurovision Song Contest 2026, Vienna, Austria. Semi-finals 12 and 14 May; Grand Final Saturday 16 May 2026."},
     "Not this Saturday, no. DuckDuckGo says the final is on Saturday 16 May in Vienna, with the semi-finals on 12 and 14 May."),
    ("la-008", "Callum", "2026-09-28 20:15", "the United Kingdom", "Is there any news about the storm that's meant to be coming?", "web", "UK storm warning latest",
     {"source": "DuckDuckGo", "text": "Met Office yellow wind warning for Wednesday across Scotland and northern England; gusts of 50-60 mph possible on coasts. Some travel disruption likely."},
     "DuckDuckGo says the Met Office has a yellow wind warning for Wednesday in Scotland and northern England, with gusts of 50 to 60 mph on the coasts. Worth checking before any travel."),
    ("la-009", "Lily", "2026-10-25 15:05", "the United Kingdom", "When's the next bank holiday?", "web", "next UK bank holiday",
     {"source": "DuckDuckGo", "text": "Upcoming bank holidays in England and Wales: Christmas Day, Friday 25 December 2026; Boxing Day, Monday 28 December 2026 (substitute day)."},
     "The next one is Christmas Day, Friday 25 December, according to DuckDuckGo. Boxing Day falls on a Saturday this year, so the extra day off is Monday 28 December."),
    ("la-j01", "ユキ", "2026-06-09 08:05", "Japan", "次の衆議院選挙はいつ？", "web", "次の衆議院選挙 日程",
     {"source": "DuckDuckGo", "text": "衆議院議員の任期は4年。解散がない場合、次の総選挙は任期満了の2028年10月までに行われる。"},
     "DuckDuckGoによると、解散がなければ任期満了の2028年10月までに行われるみたい。解散があれば、もっと早くなることもあるよ。"),
]

# Settled facts in the same breath as changing ones: answer the settled part, look up the rest.
MIXED = [
    ("lm-001", "Ade", "2026-05-27 09:05", "the United Kingdom", "Who was the first woman Prime Minister, and who's in charge now?",
     {"reply": "The first was Margaret Thatcher, from 1979. Who's in charge now I'd better check online, so I don't give you an old answer.", "lookup": {"kind": "web", "query": "current UK Prime Minister"}}),
    ("lm-002", "Isla", "2026-11-03 16:45", "", "How tall is Mount Everest?",
     "About 8,849 metres, which is the figure China and Nepal agreed on in 2020. It's the highest mountain above sea level."),
    ("lm-003", "Leo", "2026-10-11 19:35", "", "When did the Berlin Wall fall?",
     "On 9 November 1989, when the border crossings opened and people started taking the wall apart. Germany was reunified the next year, in October 1990."),
]


def main():
    out = []
    for i, (eid, person, now, q, kind, query, notes, country) in enumerate(ASKS + ASKS_JA):
        ja = eid.startswith("lk-j")
        ex = {"id": eid, "cat": "lookup", "person": person, "now": now, "notes": notes,
              "turns": [["u", q], ["a", {"reply": (ASK_JA if ja else ASK)[i % (3 if ja else 6)],
                                         "lookup": {"kind": kind, "query": query}}]]}
        if country:
            ex["country"] = country
        if ja:
            ex["cat"] = "japanese"
        out.append(ex)
    for i, (eid, person, now, country, q, kind, query, found, final) in enumerate(ANSWERS):
        ja = eid.startswith("la-j")
        ask = {"reply": (ASK_JA if ja else ASK)[i % (3 if ja else 6)], "lookup": {"kind": kind, "query": query}}
        results = brain.lookup_turn(found, query, q)["content"]
        ex = {"id": eid, "cat": "japanese" if ja else "lookup", "person": person, "now": now,
              "turns": [["u", q], ["a", ask], ["u", results], ["a", final]]}
        if country:
            ex["country"] = country
        out.append(ex)
    for eid, person, now, country, q, a in MIXED:
        ex = {"id": eid, "cat": "lookup", "person": person, "now": now, "turns": [["u", q], ["a", a]]}
        if country:
            ex["country"] = country
        out.append(ex)
    path = os.path.join(HERE, "data", "lookups.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for ex in out:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    print(len(out), "examples ->", path)


main()
