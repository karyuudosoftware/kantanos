# Runs as root in the test VM: details behind the black screen from the stick's logs.
VAR=$(find /mnt/stick -maxdepth 5 -type d -path '*/deploy/*/var' | head -1)
J="$VAR/log/journal"
jc() { journalctl -D "$J" --no-pager -o short-monotonic "$@" 2>/dev/null; }
echo "== how the stick was connected (boot -1)"
jc -b -1 -k | grep -i -E "usb [0-9.-]+: new .* USB device|Patriot|usb-storage|sd[a-z]: .*logical blocks|UAS|uas" | cut -c1-170 | head -12
echo "== stalls reported by the kernel (all boots)"
for b in -3 -2 -1 0; do echo "boot $b: $(jc -b $b -k | grep -c -i -E 'blocked for more than|hung_task|task .* blocked')"; done
jc -b -1 -k | grep -i -E "blocked for more than" | cut -c1-150 | head -5
echo "== login screen display server (boot -1)"
jc -b -1 | grep -i -E "kwin|plasma-login|plasmalogin|startplasma" | grep -v audit | cut -c1-200 | head -30
echo "== login screen display server (boot 0)"
jc -b 0 | grep -i -E "kwin|plasma-login|startplasma" | grep -v audit | cut -c1-200 | head -12
echo "== starter apps service (boot -1)"
jc -b -1 -u kantanos-flatpak-setup.service | cut -c1-170 | head -8
jc -b -1 | grep -i -E "flatpak" | grep -v audit | cut -c1-170 | head -10
echo "== what was busy when the login screen started (boot -1, 100-320 s)"
jc -b -1 | awk -F'[][]' '{t=$2+0} t>100 && t<320' | grep -i -E "Starting |Started |Finished |timed out|Failed" | grep -v audit | cut -c1-150 | head -40
echo "== tuned crash"
jc -b -1 | grep -i -E "tuned" | grep -v audit | cut -c1-200 | head -6
