#!/bin/bash
# Sets the time zone inside a built run-from-USB image (the installer would normally ask).
#   set-timezone.sh <disk.raw> <Zone/Name>      e.g. America/Toronto
# Without a zone the system runs on UTC, and with a Windows-style local hardware clock it
# would then show the wrong time and set Windows' clock wrong too.
set -euo pipefail
IMG="$1"; ZONE="$2"
[ -f "/usr/share/zoneinfo/$ZONE" ] || { echo "unknown time zone: $ZONE"; exit 2; }
LOOP=$(losetup --find --show --partscan "$IMG")
trap 'umount /mnt/kantan-img 2>/dev/null || true; losetup -d "$LOOP" 2>/dev/null || true' EXIT
udevadm settle 2>/dev/null || sleep 2
PART=""
for p in "$LOOP"p*; do
    if [ "$(blkid -o value -s TYPE "$p" 2>/dev/null)" = btrfs ]; then PART="$p"; fi
done
[ -n "$PART" ] || { echo "no btrfs partition found in $IMG"; exit 1; }
mkdir -p /mnt/kantan-img
mount -t btrfs "$PART" /mnt/kantan-img
# The live configuration of the deployment is <subvol>/ostree/deploy/<os>/deploy/<id>/etc
# (not .../<id>/usr/etc, the read-only defaults). A shell glob never crosses a "/".
ETC=""
for d in /mnt/kantan-img/*/ostree/deploy/*/deploy/*/etc /mnt/kantan-img/ostree/deploy/*/deploy/*/etc; do
    [ -d "$d" ] && [ -f "$d/os-release" -o -L "$d/os-release" -o -f "$d/adjtime" ] && { ETC="$d"; break; }
done
[ -n "$ETC" ] || { echo "no deployment found"; exit 1; }
ln -sfn "../usr/share/zoneinfo/$ZONE" "$ETC/localtime"
setfattr -h -n security.selinux -v "system_u:object_r:locale_t:s0" "$ETC/localtime"
echo "time zone set: $(readlink "$ETC/localtime")  ($(getfattr -h --only-values -n security.selinux "$ETC/localtime" 2>/dev/null))"
grep -q LOCAL "$ETC/adjtime" && echo "hardware clock: local time (same as Windows)" || echo "hardware clock: UTC"
sync
