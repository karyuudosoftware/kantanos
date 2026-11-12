#!/bin/bash
# Logs the test user in at the graphical login screen, then screenshots.
HERE="$(cd "$(dirname "$0")" && pwd)"
Q="python3 $HERE/qmp.py"
$Q key shift
sleep 8
$Q type kantan
bash "$HERE/shot.sh" login-prompt 2 | head -1
sleep 2
$Q key ret
bash "$HERE/shot.sh" "${1:-desktop-01}" "${2:-150}" | head -1
