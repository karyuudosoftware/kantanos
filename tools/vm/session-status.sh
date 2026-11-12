#!/bin/bash
# Prints the state of the graphical session inside the VM (via the serial console).
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 "$HERE/serial.py" --timeout 180 '
echo "graphical sessions: $(loginctl list-sessions --no-pager | grep -c "kantan.*seat0")";
pgrep -a -u kantan "kwin|plasmashell|startplasma|fcitx" | cut -c1-80;
echo "auth failures: $(journalctl -b --no-pager -o cat | grep -c -i "ERROR_AUTHENTICATION")";
echo "segfaults: $(journalctl -b -k --no-pager | grep -c segfault)";
journalctl -b --user --no-pager -o cat 2>/dev/null | grep -i -E "layout|script|error.*(panel|applet|plasmoid)|kantan" | tail -15'
