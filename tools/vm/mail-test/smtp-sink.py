#!/usr/bin/env python3
"""A pretend outgoing mail server for testing Kan-chan's email in the VM: accepts every email
and saves it to output/vm/sent-mail/ instead of sending it anywhere.

  python tools/vm/mail-test/smtp-sink.py      (listens on 127.0.0.1:8025; the VM reaches it as 10.0.2.2:8025)
"""
import os
import socketserver
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(ROOT, "output", "vm", "sent-mail")


class Handler(socketserver.StreamRequestHandler):
    def say(self, line):
        self.wfile.write((line + "\r\n").encode())

    def handle(self):
        self.say("220 test sink")
        rcpt = []
        while True:
            line = self.rfile.readline()
            if not line:
                return
            cmd = line.decode(errors="replace").strip()
            up = cmd.upper()
            if up.startswith(("EHLO", "HELO")):
                self.say("250-test sink\r\n250 8BITMIME")
            elif up.startswith("RCPT TO"):
                rcpt.append(cmd[8:].strip())
                self.say("250 ok")
            elif up == "DATA":
                self.say("354 go on")
                data = []
                while True:
                    l = self.rfile.readline()
                    if not l or l in (b".\r\n", b".\n"):
                        break
                    data.append(l)
                os.makedirs(OUT, exist_ok=True)
                name = os.path.join(OUT, time.strftime("%H%M%S") + f"-{len(os.listdir(OUT))}.eml")
                with open(name, "wb") as f:
                    f.write(b"X-Test-Recipients: " + ", ".join(rcpt).encode() + b"\r\n" + b"".join(data))
                print("saved", name, "to", rcpt, flush=True)
                rcpt = []
                self.say("250 saved")
            elif up == "QUIT":
                self.say("221 bye")
                return
            else:
                self.say("250 ok")


class Server(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    print("listening on 127.0.0.1:8025", flush=True)
    Server(("127.0.0.1", 8025), Handler).serve_forever()
