#!/bin/bash
# do.sh <shot-name> <wait-seconds> [qmp args...] — run one qmp action, wait, screenshot.
HERE="$(cd "$(dirname "$0")" && pwd)"
name=$1; wait=$2; shift 2
[ $# -gt 0 ] && python3 "$HERE/qmp.py" "$@"
bash "$HERE/shot.sh" "$name" "$wait" | head -1
