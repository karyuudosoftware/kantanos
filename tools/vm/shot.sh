#!/bin/bash
# shot.sh <name> [wait-seconds]  — waits, then saves a VM screenshot to output/shots/<name>.png
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="$HERE/../../output/shots"
mkdir -p "$DEST"
sleep "${2:-0}"
python3 "$HERE/qmp.py" shot "/root/kantan-out/run/$1.png"
cp "/root/kantan-out/run/$1.png" "$DEST/$1.png"
echo "saved $1.png; serial tail:"
tail -c 600 /root/kantan-out/run/serial.log 2>/dev/null | tr -d '\r' | tail -5
