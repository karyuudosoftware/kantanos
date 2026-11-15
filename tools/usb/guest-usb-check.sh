# Runs as root in the VM booted from the USB image: clock, time zone and first-boot state.
timedatectl 2>/dev/null | grep -E "Local time|Time zone|RTC in local"
echo "selinux denials for localtime: $(journalctl -b --no-pager -o cat 2>/dev/null | grep -c 'avc:.*localtime')"
grep -E "^KANTAN_(VERSION|BUILD|IMAGE)" /usr/lib/os-release
systemctl is-failed bazzite-hardware-setup.service plasmalogin.service 2>/dev/null | tr '\n' ' '; echo
journalctl -b -u bazzite-hardware-setup --no-pager -o cat | grep -E "karg|Reboot|No karg" | tail -3
