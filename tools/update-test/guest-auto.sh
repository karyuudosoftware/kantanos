# Runs inside the test VM: trigger the same service the daily 4 am timer starts.
echo "== before"; grep -E "^KANTAN_VERSION" /usr/lib/os-release
systemctl start uupd.service; echo "uupd exit: $?"
journalctl -u uupd.service -b --no-pager -o cat | grep -v '^{' | tail -8
journalctl -u uupd.service -b --no-pager -o cat | grep -o '"msg":"[^"]*"' | tail -12
bootc status --format json | jq -r '"staged:   " + (.status.staged.image.imageDigest // "none")'
