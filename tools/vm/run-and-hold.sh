#!/bin/bash
# Starts the VM and stays in the foreground until it exits, so WSL keeps the distro alive.
HERE="$(cd "$(dirname "$0")" && pwd)"
bash "$HERE/run-vm.sh" || exit 1
PID=$(cat /root/kantan-out/run/qemu.pid)
while kill -0 "$PID" 2>/dev/null; do sleep 20; done
echo VM_EXITED
