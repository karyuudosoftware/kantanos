#!/bin/bash
# Builds an installer ISO (Anaconda) for localhost/kantanos:latest and copies it to output/iso/.
# Run as root inside the Fedora build environment. Takes 15-25 minutes.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/../image-ref.sh"   # LOCAL_IMAGE: the update address when set, else localhost/kantanos
OUT=/root/kantan-iso
rm -rf "$OUT" && mkdir -p "$OUT"
bash "$HERE/make-iso-config.sh" "$OUT/config.toml"
# The builder is pinned: its 24 Nov 2026 release names the system by its own ID ("bazzite-45")
# and refuses it ("requested repository not found"). This one (9 Nov 2026) builds it. Upstream
# has stopped work on this builder; Bazzite itself now makes its ISOs with Titanoboa.
BIB=quay.io/centos-bootc/bootc-image-builder@sha256:dab86ee6b46dcade411b37f4e70b07d93b6a06da0dbfec6fe89247a220e0d9f8
podman run --rm --privileged \
    --security-opt label=type:unconfined_t \
    -v "$OUT":/output \
    -v "$OUT/config.toml":/config.toml:ro \
    -v /var/lib/containers/storage:/var/lib/containers/storage \
    "$BIB" \
    --type anaconda-iso --rootfs btrfs \
    "$LOCAL_IMAGE:latest" > /root/iso.log 2>&1 || { tail -40 /root/iso.log; exit 1; }
DEST="$HERE/../../output/iso"
mkdir -p "$DEST"
VERSION=$(podman run --rm --entrypoint bash "$LOCAL_IMAGE:latest" -c '. /usr/lib/os-release; echo $KANTAN_VERSION')
# KantanOS name in the installer title and boot menus (tools/iso/brand-iso.sh)
for tool in xorriso mtools cpio gawk squashfs-tools; do rpm -q "$tool" >/dev/null || dnf5 -y -q install "$tool"; done
bash "$HERE/brand-iso.sh" "$OUT/bootiso/install.iso" "$DEST/KantanOS-$VERSION-x86_64.iso" "$VERSION"
ls -la "$DEST"
