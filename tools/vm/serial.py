#!/usr/bin/env python3
"""Run a command on the VM's serial console (logs in as the test user if needed).

  serial.py [--timeout N] '<shell command>'
  serial.py [--timeout N] --script <local-file.sh>
  serial.py [--timeout N] --root-script <local-file.sh>    same, run as root (sudo)
"""
import base64, os, re, socket, sys, time, uuid

SOCK = os.environ.get("KANTAN_SERIAL", "tcp:127.0.0.1:4445" if os.name == "nt" else "/root/kantan-out/run/serial.sock")
USER = PASSWORD = "kantan"   # throwaway test account from tools/vm/config.toml
ANSI = re.compile(rb"\x1b\][^\x07\x1b]*(\x07|\x1b\\)|\x1b\[[0-9;?]*[A-Za-z]|\x1b[PX^_].*?\x1b\\|\r")


def read_until(s, pattern, timeout):
    buf, end = b"", time.time() + timeout
    while time.time() < end:
        try:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
            if re.search(pattern, ANSI.sub(b"", buf)):
                return ANSI.sub(b"", buf), True
        except socket.timeout:
            pass
    return ANSI.sub(b"", buf), False


def main():
    args = sys.argv[1:]
    timeout = 120
    if args and args[0] == "--timeout":
        timeout = int(args[1]); args = args[2:]
    if args and args[0] == "--root-script":
        body = open(args[1], "rb").read().replace(b"\r\n", b"\n")
        cmd = ("echo " + base64.b64encode(body).decode() + " | base64 -d > /tmp/kantan-root.sh; "
               "echo " + PASSWORD + " | sudo -S -p '' bash /tmp/kantan-root.sh")
    elif args and args[0] == "--script":
        # Run a whole local script file in the guest; base64 avoids every quoting problem.
        body = open(args[1], "rb").read().replace(b"\r\n", b"\n")
        cmd = "echo " + base64.b64encode(body).decode() + " | base64 -d | bash"
    else:
        cmd = " ".join(args)
    if SOCK.startswith("tcp:"):
        host, port = SOCK[4:].rsplit(":", 1)
        s = socket.create_connection((host, int(port)))
    else:
        s = socket.socket(socket.AF_UNIX); s.connect(SOCK)
    s.settimeout(2)

    s.sendall(b"\n")
    out, _ = read_until(s, rb"login: $|[$#] $", 20)
    if re.search(rb"login: $", out):
        s.sendall(USER.encode() + b"\n")
        read_until(s, rb"Password: $", 60)
        s.sendall(PASSWORD.encode() + b"\n")
        out, ok = read_until(s, rb"[$#] $", 180)
        if not ok:
            print("LOGIN FAILED OR TIMED OUT:\n" + out.decode(errors="replace")[-800:]); sys.exit(2)

    mark = "END" + uuid.uuid4().hex[:8]
    s.sendall(f"stty -echo cols 250; {cmd}; echo; echo {mark}=$?\n".encode())
    out, ok = read_until(s, mark.encode() + rb"=\d+", timeout)
    text = out.decode(errors="replace")
    text = text.split("\n", 1)[1] if "\n" in text else text
    print(text.strip())
    if not ok:
        print("[timed out]"); sys.exit(3)


if __name__ == "__main__":
    main()
