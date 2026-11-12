#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 "$HERE/serial.py" --timeout 300 '
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus;
pkill -u kantan -f "steam|bazzite-portal|yad|zenity" ; sleep 1;
P=$(pgrep -u kantan -x plasmashell);
echo "main thread: $(ps -L -o tid,stat,pcpu,time,comm -p $P | awk -v p=$P "\$1==p")";
echo "threads: $(ls /proc/$P/task | wc -l)";
ps -L -o comm= -p $P | sort | uniq -c | sort -rn | head -8;
echo "== ping"; timeout 90 busctl --user call org.kde.plasmashell /PlasmaShell org.freedesktop.DBus.Peer Ping; echo "ping rc=$?";
echo "== load"; cat /proc/loadavg; ps -eo pcpu,comm --sort=-pcpu | head -8'
