#!/bin/bash
# wait-for.sh <regex> <max-seconds> <shot-name> — waits until the serial log matches, then screenshots.
HERE="$(cd "$(dirname "$0")" && pwd)"
LOG=/root/kantan-out/run/serial.log
end=$((SECONDS + ${2:-300}))
while [ $SECONDS -lt $end ]; do
    if tr -d '\r' < "$LOG" | grep -a -q -E "$1"; then echo "MATCHED: $1"; break; fi
    kill -0 "$(cat /root/kantan-out/run/qemu.pid)" 2>/dev/null || { echo "VM is not running"; exit 1; }
    sleep 10
done
echo "--- last distinct service lines"
tr -d '\r' < "$LOG" | grep -a -E 'Started|Finished|Reached|FAILED|login:' | sed 's/\x1b\[[0-9;]*m//g' | tail -12
bash "$HERE/shot.sh" "${3:-wait}" 0 | head -1
