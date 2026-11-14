#!/bin/bash
# Builds a run-from-USB KantanOS: a raw disk image that is written straight to a USB drive
# (32 GB or larger) and booted, with no installer. Changes are kept on the drive.
#
#   make-usb.sh [username]        default username: admin
#
# There is no installer to create an account, so one is baked in. Its temporary password is
# generated here, written to output/usb/LOGIN.txt (not in git) and only its hash goes into
# the image. Run as root inside the Fedora build environment. Takes 15-25 minutes.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/../image-ref.sh"
USERNAME="${1:-admin}"
DEST="$HERE/../../output/usb"
WORK=/root/kantan-usb
mkdir -p "$DEST"
rm -rf "$WORK" && mkdir -p "$WORK"

if [ ! -s "$DEST/LOGIN.txt" ]; then
    PASSWORD="$(python3 -c 'import secrets; print("-".join(secrets.choice(["maple","river","stone","cedar","amber","cloud","falcon","harbor","meadow","pine","sparrow","tide","willow","ember","frost","lantern"]) for _ in range(3)) + "-" + str(secrets.randbelow(90) + 10))')"
    printf 'KantanOS USB test drive\n\nUser name: %s\nTemporary password: %s\n\nChange it after logging in: System Settings > Users.\n' "$USERNAME" "$PASSWORD" > "$DEST/LOGIN.txt"
fi
PASSWORD="$(sed -n 's/^Temporary password: //p' "$DEST/LOGIN.txt")"
# The build environment has no openssl; the KantanOS image does.
HASH="$(printf '%s' "$PASSWORD" | podman run --rm -i --entrypoint openssl "$LOCAL_IMAGE:latest" passwd -6 -stdin)"
case "$HASH" in '$6$'*) ;; *) echo "could not hash the password"; exit 1 ;; esac

# 25 GiB root + boot partitions fits a nominal 32 GB stick (about 28.6 GiB) with room to spare.
cat > "$WORK/config.toml" <<TOML
[[customizations.user]]
name = "$USERNAME"
password = '$HASH'
groups = ["wheel"]

[[customizations.filesystem]]
mountpoint = "/"
minsize = "25 GiB"
TOML

podman run --rm --privileged --pull=newer \
    --security-opt label=type:unconfined_t \
    -v "$WORK":/output \
    -v "$WORK/config.toml":/config.toml:ro \
    -v /var/lib/containers/storage:/var/lib/containers/storage \
    quay.io/centos-bootc/bootc-image-builder:latest \
    --type raw --rootfs btrfs \
    "$LOCAL_IMAGE:latest" > /root/usb.log 2>&1 || { tail -40 /root/usb.log; exit 1; }
rm -f "$WORK/config.toml"

VERSION=$(podman run --rm --entrypoint bash "$LOCAL_IMAGE:latest" -c '. /usr/lib/os-release; echo "$KANTAN_VERSION-$KANTAN_BUILD"')
OUT="$DEST/KantanOS-$VERSION-usb.img"
rm -f "$DEST"/KantanOS-*-usb.img
cp "$WORK/image/disk.raw" "$OUT"
rm -rf "$WORK"
ls -la "$DEST"
echo "image: $OUT ($(du -h --apparent-size "$OUT" | cut -f1))"
