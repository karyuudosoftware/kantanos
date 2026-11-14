# Runs as root in the test VM after guest-read-stick.sh: per-boot summary of the stick's logs.
VAR=$(find /mnt/stick -maxdepth 5 -type d -path '*/deploy/*/var' | head -1)
echo "var: $VAR"
J="$VAR/log/journal"
jc() { journalctl -D "$J" --no-pager -o short-monotonic "$@" 2>/dev/null; }
echo "== machine"; jc -b 0 -k | grep -m3 -i -E "DMI:|Secure boot|secureboot" | cut -c1-160
for b in -3 -2 -1 0; do
    echo; echo "################ boot $b"
    jc -b $b | grep -m1 -E "Command line" | cut -c1-260
    echo "-- milestones"
    jc -b $b | grep -E "Startup finished|Reached target (Graphical|Multi-User)|hardware-setup|Rebooting|reboot: |Starting Plasma Login|plasmalogin|Started .*Login Manager|kwin_wayland|Shutting down|Power key|systemd-logind.*(Power|Session)" | cut -c1-190 | head -28
    echo "-- nvidia / drm"
    jc -b $b -k | grep -i -E "nvidia|NVRM|nouveau|simpledrm|\[drm\]|fb0|Lockdown|module verification|taint" | cut -c1-170 | head -16
    echo "-- errors"
    jc -b $b -p 3 | grep -v -E "^--|bluetooth|Bluetooth|ACPI|thermal|pcieport|usb [0-9-]+:|dbus-broker" | cut -c1-190 | tail -14
done
