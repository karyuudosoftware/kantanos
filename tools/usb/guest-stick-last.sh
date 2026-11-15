# Runs as root in the test VM: the stick's connection speed and the last minutes of its newest boot.
VAR=$(find /mnt/stick -maxdepth 5 -type d -path '*/deploy/*/var' | head -1)
J="$VAR/log/journal"
jc() { journalctl -D "$J" --no-pager "$@" 2>/dev/null; }
echo "== stick connection (newest boot)"
jc -b 0 -k -o short-monotonic | grep -B1 -A3 -i -E "Product: DataTraveler|Manufacturer: Kingston" | cut -c1-150 | head -10
echo "== clock jumps (newest boot)"
jc -b 0 -o short-iso | grep -i -E "time has been changed|Time jumped|synchroniz" | cut -c1-150 | head -5
echo "== last 40 lines of the newest boot"
jc -b 0 -o short-iso | grep -v -E "audit\[|audit:" | tail -40 | cut -c1-190
