#!/bin/bash
# Shows which image address the newest installer ISO will make an installed PC follow.
ISO=$(ls -t /mnt/d/CLAUDE_Projects/kantanos/output/iso/*.iso | head -1)
echo "ISO: $ISO ($(du -h "$ISO" | cut -f1))"
M=$(mktemp -d); mount -o loop,ro "$ISO" "$M" || exit 1
for f in "$M"/osbuild.ks "$M"/*.ks; do [ -f "$f" ] && { echo "== $f"; cat "$f"; }; done 2>/dev/null | sort -u | head -40
umount "$M"; rmdir "$M"
podman run --rm --entrypoint bash ghcr.io/karyuudosoftware/kantanos:latest -c 'grep -E "^KANTAN_" /usr/lib/os-release; jq -c ".transports.docker[\"ghcr.io/karyuudosoftware/kantanos\"]" /etc/containers/policy.json'
