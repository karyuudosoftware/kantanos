// Kan-chan email helper: Thunderbird does the email (every account it has, Outlook and Gmail
// sign-ins included); Kan-chan on this PC asks for things through a small local server
// (127.0.0.1 only, with this person's own token from config.js). Nothing else is contacted.
// Kan-chan asks the person before anything is sent or binned; this side only does what it is told.
"use strict";

const BASE = "http://127.0.0.1:" + KANCHAN.port;
const MAX_LIST = 25;

function who(author) {
  const m = /^\s*"?([^"<]*?)"?\s*<([^>]+)>\s*$/.exec(author || "");
  return m ? {name: m[1].trim() || m[2], address: m[2].trim()} : {name: (author || "").trim(), address: (author || "").trim()};
}

function head(h) {
  const from = who(h.author);
  return {id: h.id, from: from.name, address: from.address, subject: h.subject || "",
          date: h.date ? new Date(h.date).toISOString() : "", read: !!h.read,
          account: h.folder ? h.folder.accountId : ""};
}

function isInbox(f) {
  return (f.specialUse && f.specialUse.includes("inbox")) || f.type === "inbox";
}

async function inboxes() {
  const found = [];
  const walk = (folders) => {
    for (const f of folders || []) {
      if (isInbox(f)) found.push(f);
      walk(f.subFolders);
    }
  };
  for (const a of await messenger.accounts.list(true)) {
    walk(a.folders);
  }
  return found;
}

async function listFolder(folder, query) {
  const out = [];
  let page;
  try {
    page = await messenger.messages.query(Object.assign({folderId: folder.id}, query));
  } catch (e) {
    page = await messenger.messages.query(Object.assign({folder: folder}, query));   // older Thunderbird
  }
  while (page) {
    out.push(...page.messages);
    if (!page.id || out.length >= 200) break;
    page = await messenger.messages.continueList(page.id);
  }
  return out;
}

async function messages(unreadOnly, days) {
  const query = {};
  if (unreadOnly) query.unread = true;
  if (days) query.fromDate = new Date(Date.now() - days * 86400000);
  let all = [];
  for (const f of await inboxes()) {
    all = all.concat(await listFolder(f, query));
  }
  all.sort((a, b) => new Date(b.date) - new Date(a.date));
  return all.slice(0, MAX_LIST).map(head);
}

function stripHtml(html) {
  const doc = new DOMParser().parseFromString(html, "text/html");
  for (const el of doc.querySelectorAll("style, script, head")) el.remove();
  for (const el of doc.querySelectorAll("br, p, div, li, tr, h1, h2, h3")) el.append("\n");
  return doc.body ? doc.body.textContent : "";
}

async function bodyText(id) {
  let plain = "", html = "";
  if (messenger.messages.listInlineTextParts) {
    try {
      for (const p of await messenger.messages.listInlineTextParts(id)) {
        if (p.contentType === "text/plain" && !plain) plain = p.content;
        if (p.contentType === "text/html" && !html) html = p.content;
      }
    } catch (e) { /* fall back below */ }
  }
  if (!plain && !html) {
    const walk = (part) => {
      if (!part) return;
      if (part.body && part.contentType === "text/plain" && !plain) plain = part.body;
      if (part.body && part.contentType === "text/html" && !html) html = part.body;
      for (const p of part.parts || []) walk(p);
    };
    walk(await messenger.messages.getFull(id));
  }
  return plain || stripHtml(html);
}

async function contacts(name) {
  const out = [], seen = new Set();
  const add = (n, addr) => {
    if (addr && !seen.has(addr.toLowerCase())) {
      seen.add(addr.toLowerCase());
      out.push({name: n || addr, address: addr});
    }
  };
  try {
    for (const c of await messenger.contacts.quickSearch(name)) {
      const p = c.properties || {};
      const n = p.DisplayName || [p.FirstName, p.LastName].filter(Boolean).join(" ");
      add(n, p.PrimaryEmail);
      add(n, p.SecondEmail);
    }
  } catch (e) { /* no address books */ }
  if (!out.length) {          // people who have emailed this person recently
    const words = name.toLowerCase().split(/\s+/).filter(Boolean);
    for (const m of await messages(false, 120)) {
      const n = m.from.toLowerCase();
      if (words.every((w) => n.split(/[\s.,]+/).includes(w))) add(m.from, m.address);
    }
  }
  return out.slice(0, 6);
}

async function send(tab) {
  const r = await messenger.compose.sendMessage(tab.id, {mode: "sendNow"});
  return r === false ? {sent: false} : {sent: true};
}

const OPS = {
  async status() {
    const accounts = await messenger.accounts.list(false);
    return {accounts: accounts.filter((a) => a.type !== "none").map((a) => a.name),
            version: (await messenger.runtime.getBrowserInfo()).version};
  },
  async unread() { return messages(true, 0); },
  async recent(a) { return messages(false, a.days || 3); },
  async read(a) {
    const h = await messenger.messages.get(a.id);
    const text = await bodyText(a.id);
    if (a.markRead) await messenger.messages.update(a.id, {read: true});
    return Object.assign(head(h), {text: text});
  },
  async reply(a) {
    const tab = await messenger.compose.beginReply(a.id, "replyToSender", {plainTextBody: a.text, isPlainText: true});
    return send(tab);
  },
  async write(a) {
    const tab = await messenger.compose.beginNew(undefined, {to: [a.to], subject: a.subject, plainTextBody: a.text,
                                                              isPlainText: true});
    return send(tab);
  },
  async bin(a) {                       // to the bin (Trash), never deleted for good
    await messenger.messages.delete([a.id], false);
    return {binned: true};
  },
  async contacts(a) { return contacts(a.name || ""); },
};

async function post(path, body) {
  return fetch(BASE + path, {method: "POST", headers: {"Content-Type": "application/json",
               "X-Kanchan-Token": KANCHAN.token}, body: JSON.stringify(body)});
}

async function loop() {
  for (;;) {
    let job = null;
    try {
      const r = await fetch(BASE + "/poll", {headers: {"X-Kanchan-Token": KANCHAN.token}});
      if (r.status === 200) job = await r.json();
      else if (r.status !== 204) await new Promise((ok) => setTimeout(ok, 5000));
    } catch (e) {               // Kan-chan isn't open: try again in a little while
      await new Promise((ok) => setTimeout(ok, 5000));
      continue;
    }
    if (!job) continue;
    let result;
    try {
      if (!OPS[job.op]) throw new Error("unknown request");
      result = {id: job.id, ok: true, data: await OPS[job.op](job.args || {})};
    } catch (e) {
      result = {id: job.id, ok: false, error: String(e && e.message || e)};
    }
    try { await post("/result", result); } catch (e) { /* Kan-chan closed meanwhile */ }
  }
}

messenger.messages.onNewMailReceived.addListener((folder, list) => {
  if (!isInbox(folder)) return;
  post("/event", {kind: "new", messages: list.messages.map(head)}).catch(() => {});
});

loop();
