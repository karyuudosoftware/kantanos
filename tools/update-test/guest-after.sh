# Runs inside the test VM after a restart: which version is running, and what can be undone.
echo "== running now"; grep -E "^(PRETTY_NAME|KANTAN_VERSION|KANTAN_BUILD)" /usr/lib/os-release
bootc status --format json 2>/dev/null | jq -r '"booted:   " + .status.booted.image.imageDigest, "rollback: " + (.status.rollback.image.imageDigest // "none"), "staged:   " + (.status.staged.image.imageDigest // "none")'
echo "== test registry setting kept across the update"; ls /etc/containers/registries.conf.d/ | grep kantan
echo "== failed units"; systemctl --failed --no-legend | head -5
