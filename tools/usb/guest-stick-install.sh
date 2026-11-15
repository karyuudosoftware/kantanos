# Runs as root in the test VM after guest-read-stick.sh: what happened to app installs
# (Welcome app and starter apps) during the stick's boots on the real PC.
VAR=$(find /mnt/stick -maxdepth 5 -type d -path '*/deploy/*/var' | head -1)
J="$VAR/log/journal"
jc() { journalctl -D "$J" --no-pager -o short-iso "$@" 2>/dev/null; }
echo "== boots"; journalctl -D "$J" --list-boots --no-pager 2>/dev/null | tail -8
echo "== installed Flatpak apps on the stick"
ls "$VAR/lib/flatpak/app" 2>/dev/null | tr '\n' ' '; echo
ls "$VAR/lib/flatpak/runtime" 2>/dev/null | tr '\n' ' '; echo
echo "== starter-apps marker"; ls -la "$VAR/lib/kantanos/" 2>/dev/null
echo "== starter apps service (all boots)"
jc -u kantanos-flatpak-setup.service | grep -v -E "^--" | cut -c1-170 | tail -25
echo "== NotepadNext / Welcome activity (all boots)"
jc | grep -i -E "notepadnext|kantan-app|yafti|NotepadNext" | grep -v audit | cut -c1-200 | tail -30
echo "== flatpak system helper (installs) - last 30"
jc | grep -i -E "flatpak-system-helper|FlatpakSystemHelper|flatpak\[|Installing|Pulled|deploy" | grep -v audit | cut -c1-190 | tail -30
echo "== stalls / OOM / disk errors (all boots)"
jc -k | grep -i -E "blocked for more than|Out of memory|oom-kill|I/O error|reset high-speed|reset SuperSpeed|usb .*disconnect|EXT4-fs error|BTRFS (error|warning)" | cut -c1-170 | tail -15
echo "== how the stick connected (newest boot)"
jc -b 0 -k | grep -i -E "Kingston|DataTraveler|new (high|full|SuperSpeed).*USB device" | cut -c1-160 | head -6
