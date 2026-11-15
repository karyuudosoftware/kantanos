# Runs as the test user in the VM soon after a fresh first boot: starts an app install while
# the starter apps are still downloading, the situation that looked frozen on the USB stick.
# The serial console is a terminal, so kantan-app behaves as it does in the Welcome app's
# terminal window (stdin is closed so it does not wait for Enter at the end).
echo "== starter download running?"
pgrep -af '(^|/)flatpak install' | head -2 || echo "no other download running"
echo "== install NotepadNext"
start=$(date +%s)
kantan-app install com.github.dail8859.NotepadNext </dev/null > /tmp/clash.log 2>&1
rc=$?
echo "exit $rc, took $(( $(date +%s) - start )) s"
tr '\r' '\n' < /tmp/clash.log | grep -v '^\s*$' | awk '!/waiting\.\.\./ || ++w<=2' | grep -v -E '^[[:space:]]*[0-9]+\.' | head -n 14
echo "== result"; flatpak list --app --columns=application
echo "== starter service log"; journalctl -b -u kantanos-flatpak-setup --no-pager -o cat | grep -E "Installing [a-z]|Pausing|All starter|retry" | tail -8
