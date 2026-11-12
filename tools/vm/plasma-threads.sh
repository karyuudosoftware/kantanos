#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 "$HERE/serial.py" --timeout 240 '
P=$(pgrep -u kantan -x plasmashell); echo "pid $P";
ps -o etimes,time,pcpu,rss -p $P;
echo "== busiest threads"; top -H -b -n 1 -p $P -w 120 | sed -n "7,22p";
echo "== windows plasmashell has"; qdbus6 org.kde.KWin /KWin org.kde.KWin.queryWindowInfo 2>/dev/null | head -0; kscreen-doctor -o 2>/dev/null | sed "s/\x1b\[[0-9;]*m//g" | head -12;
echo "== env"; tr "\0" "\n" < /proc/$P/environ | grep -E "QT_QUICK|QSG|LIBGL|KWIN|GALLIUM|MESA" ;
echo "== glx"; grep -a -m1 -E "llvmpipe|softpipe|zink" /proc/$P/maps | cut -c74-'
