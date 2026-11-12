#!/bin/bash
# Builds an installer ISO (Anaconda) for localhost/kantanos:latest and copies it to output/iso/.
# Run as root inside the Fedora build environment. Takes 15-25 minutes.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/../image-ref.sh"   # LOCAL_IMAGE: the update address when set, else localhost/kantanos
OUT=/root/kantan-iso
rm -rf "$OUT" && mkdir -p "$OUT"
cp "$HERE/iso.toml" "$OUT/config.toml"
podman run --rm --privileged --pull=newer \
    --security-opt label=type:unconfined_t \
    -v "$OUT":/output \
    -v "$OUT/config.toml":/config.toml:ro \
    -v /var/lib/containers/storage:/var/lib/containers/storage \
    quay.io/centos-bootc/bootc-image-builder:latest \
    --type anaconda-iso --rootfs btrfs \
    "$LOCAL_IMAGE:latest" > /root/iso.log 2>&1 || { tail -40 /root/iso.log; exit 1; }
DEST="$HERE/../../output/iso"
mkdir -p "$DEST"
VERSION=$(podman run --rm --entrypoint bash "$LOCAL_IMAGE:latest" -c '. /usr/lib/os-release; echo $KANTAN_VERSION')
cp "$OUT/bootiso/install.iso" "$DEST/KantanOS-$VERSION-x86_64.iso"
ls -la "$DEST"
