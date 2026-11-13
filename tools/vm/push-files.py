#!/usr/bin/env python3
"""Copies project files into the running test VM for quick try-outs (no image rebuild).

  push-files.py <local>=<guest path> [...] [-- <shell command to run afterwards>]

Guest paths starting with ~ go to the test user's home; other paths need the test user
to be able to write there. Uses the serial console helper.
"""
import base64, os, subprocess, sys, tempfile

args, after = sys.argv[1:], ""
if "--" in args:
    i = args.index("--"); after = " ".join(args[i + 1:]); args = args[:i]
lines = ["set -e"]
for pair in args:
    local, guest = pair.split("=", 1)
    data = open(local, "rb").read().replace(b"\r\n", b"\n")
    guest = guest.replace("~", "$HOME", 1) if guest.startswith("~") else guest
    lines.append(f'mkdir -p "$(dirname "{guest}")"')
    lines.append(f'echo {base64.b64encode(data).decode()} | base64 -d > "{guest}"')
    lines.append(f'echo "pushed {guest}"')
if after:
    lines.append(after)
with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False, newline="\n") as f:
    f.write("\n".join(lines) + "\n")
here = os.path.dirname(os.path.abspath(__file__))
rc = subprocess.call([sys.executable, os.path.join(here, "serial.py"), "--timeout", "120", "--script", f.name])
os.unlink(f.name)
sys.exit(rc)
