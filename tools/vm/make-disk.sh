#!/bin/bash
# Turns localhost/kantanos:latest into a bootable VM disk (qcow2) with a test user.
# Run as root inside the Fedora build environment.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
. "$HERE/../image-ref.sh"   # LOCAL_IMAGE: the update address when set, else localhost/kantanos
OUT=${KANTAN_OUT:-/root/kantan-out}
mkdir -p "$OUT"
cp "$HERE/config.toml" "$OUT/config.toml"
podman run --rm --privileged --pull=newer \
    --security-opt label=type:unconfined_t \
    -v "$OUT":/output \
    -v "$OUT/config.toml":/config.toml:ro \
    -v /var/lib/containers/storage:/var/lib/containers/storage \
    quay.io/centos-bootc/bootc-image-builder:latest \
    --type qcow2 --rootfs btrfs \
    "$LOCAL_IMAGE:latest"
ls -la "$OUT/qcow2"
