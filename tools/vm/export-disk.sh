#!/bin/bash
# Rebuilds the test disk from the current image and copies it to the Windows side
# (output/vm/disk.qcow2) so a Windows-hosted VM can boot it.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
rm -rf /root/kantan-out/qcow2 /root/kantan-out/run
bash "$HERE/make-disk.sh" > /root/disk.log 2>&1 || { tail -30 /root/disk.log; exit 1; }
DEST="$HERE/../../output/vm"
mkdir -p "$DEST"
cp /root/kantan-out/qcow2/disk.qcow2 "$DEST/disk.qcow2"
cp /usr/share/edk2/ovmf/OVMF_CODE.fd /usr/share/edk2/ovmf/OVMF_VARS.fd "$DEST/"
ls -la "$DEST"
