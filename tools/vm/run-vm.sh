#!/bin/bash
# Boots the KantanOS test disk headless in QEMU. Screenshots come from tools/vm/shot.sh.
# Uses KVM when the host offers it, otherwise slow software emulation.
set -euo pipefail
OUT=${KANTAN_OUT:-/root/kantan-out}
DISK="$OUT/qcow2/disk.qcow2"
RUN="$OUT/run"
mkdir -p "$RUN"
[ -f "$RUN/vars.fd" ] || cp /usr/share/edk2/ovmf/OVMF_VARS.fd "$RUN/vars.fd"

# Without KVM, "-cpu max" makes the guest's software renderer crash, so use a plain CPU model.
if [ -e /dev/kvm ]; then ACCEL="-accel kvm -cpu host"; else ACCEL="-accel tcg,thread=multi,tb-size=2048 -cpu Nehalem"; fi

qemu-system-x86_64 \
    -machine q35 $ACCEL -smp "${KANTAN_VM_CPUS:-12}" -m "${KANTAN_VM_RAM:-8G}" \
    -drive if=pflash,format=raw,readonly=on,file=/usr/share/edk2/ovmf/OVMF_CODE.fd \
    -drive if=pflash,format=raw,file="$RUN/vars.fd" \
    -drive file="$DISK",if=virtio,cache=unsafe \
    -device virtio-vga,xres=1920,yres=1080 \
    -device qemu-xhci -device usb-tablet -device usb-kbd \
    -netdev user,id=n0 -device virtio-net-pci,netdev=n0 \
    -device virtio-rng-pci \
    -display none \
    -qmp unix:"$RUN/qmp.sock",server,nowait \
    -chardev socket,id=ser0,path="$RUN/serial.sock",server=on,wait=off,logfile="$RUN/serial.log" \
    -serial chardev:ser0 \
    -pidfile "$RUN/qemu.pid" -daemonize
echo "VM started, pid $(cat "$RUN/qemu.pid")"
