#!/bin/bash
# wait-boot.sh <delay> <max-seconds> — waits for the login prompt on the serial console of a fresh boot.
HERE="$(cd "$(dirname "$0")" && pwd)"
sleep "${1:-0}"
pgrep -a qemu | grep -o -E '\-cpu [A-Za-z0-9]+'
bash "$HERE/wait-for.sh" "kantanos login:" "${2:-400}" "${3:-booted}"
grep -a -c segfault /root/kantan-out/run/serial.log
