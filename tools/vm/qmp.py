#!/usr/bin/env python3
"""Tiny QMP helper for the test VM.

  qmp.py shot <file.png>      save a screenshot
  qmp.py type <text>          type text on the VM keyboard
  qmp.py key <qcode>[-<qcode>] press a key or combo, e.g. ret, ctrl-alt-f2, meta_l
  qmp.py click <x> <y>        left-click at a 1920x1080 screen position
  qmp.py quit                 power the VM off
"""
import json, os, socket, sys, time

SOCK = os.environ.get("KANTAN_QMP", "tcp:127.0.0.1:4444" if os.name == "nt" else "/root/kantan-out/run/qmp.sock")

KEYMAP = {" ": "spc", "-": "minus", "=": "equal", ".": "dot", ",": "comma", "/": "slash",
          ";": "semicolon", "'": "apostrophe", "\n": "ret", "\\": "backslash",
          "[": "bracket_left", "]": "bracket_right", "`": "grave_accent"}
SHIFTED = {"_": "minus", "+": "equal", ":": "semicolon", "!": "1", "@": "2", "#": "3", "$": "4",
           "%": "5", "^": "6", "&": "7", "*": "8", "(": "9", ")": "0", "?": "slash", '"': "apostrophe",
           "|": "backslash", ">": "dot", "<": "comma", "~": "grave_accent", "{": "bracket_left", "}": "bracket_right"}


class Qmp:
    def __init__(self):
        if SOCK.startswith("tcp:"):
            host, port = SOCK[4:].rsplit(":", 1)
            self.s = socket.create_connection((host, int(port)))
        else:
            self.s = socket.socket(socket.AF_UNIX)
            self.s.connect(SOCK)
        self.f = self.s.makefile("rw")
        self.f.readline()
        self.cmd("qmp_capabilities")

    def cmd(self, name, **args):
        msg = {"execute": name}
        if args:
            msg["arguments"] = args
        self.f.write(json.dumps(msg) + "\n")
        self.f.flush()
        while True:
            r = json.loads(self.f.readline())
            if "return" in r or "error" in r:
                if "error" in r:
                    raise SystemExit(f"QMP error: {r['error']}")
                return r["return"]

    def keys(self, qcodes, hold=80):
        self.cmd("send-key", keys=[{"type": "qcode", "data": k} for k in qcodes], **{"hold-time": hold})
        time.sleep(float(os.environ.get("KANTAN_KEY_DELAY", "0.4")))


def main():
    q = Qmp()
    op = sys.argv[1]
    if op == "shot":
        q.cmd("screendump", filename=sys.argv[2], format="png")
    elif op == "type":
        for ch in " ".join(sys.argv[2:]):
            if ch in SHIFTED:
                q.keys(["shift", SHIFTED[ch]])
            elif ch.isupper():
                q.keys(["shift", ch.lower()])
            else:
                q.keys([KEYMAP.get(ch, ch)])
    elif op == "key":
        q.keys(sys.argv[2].split("-"))
    elif op == "click":
        x, y = int(sys.argv[2]), int(sys.argv[3])
        ax, ay = x * 32767 // 1920, y * 32767 // 1080
        q.cmd("input-send-event", events=[
            {"type": "abs", "data": {"axis": "x", "value": ax}},
            {"type": "abs", "data": {"axis": "y", "value": ay}}])
        time.sleep(0.2)
        for down in (True, False):
            q.cmd("input-send-event", events=[{"type": "btn", "data": {"down": down, "button": "left"}}])
            time.sleep(0.1)
    elif op == "drag":   # drag x1 y1 x2 y2
        x1, y1, x2, y2 = (int(v) for v in sys.argv[2:6])
        def move(x, y):
            q.cmd("input-send-event", events=[
                {"type": "abs", "data": {"axis": "x", "value": x * 32767 // 1920}},
                {"type": "abs", "data": {"axis": "y", "value": y * 32767 // 1080}}])
            time.sleep(0.08)
        move(x1, y1); time.sleep(0.2)
        q.cmd("input-send-event", events=[{"type": "btn", "data": {"down": True, "button": "left"}}])
        for i in range(1, 11):
            move(x1 + (x2 - x1) * i // 10, y1 + (y2 - y1) * i // 10)
        time.sleep(0.2)
        q.cmd("input-send-event", events=[{"type": "btn", "data": {"down": False, "button": "left"}}])
    elif op == "quit":
        q.cmd("system_powerdown")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
