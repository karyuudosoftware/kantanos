#!/bin/bash
# Finishes an installer ISO from bootc-image-builder for KantanOS:
#   - images/product.img: the installer's own way to rebrand itself (its start-up code applies
#     it automatically). Its .buildstamp names the product "KantanOS" with KantanOS's version,
#     instead of the Fedora release number ("KANTANOS 45 INSTALLATION").
#   - the boot menus ("Install KantanOS 45" -> "Install KantanOS"): BIOS (boot/grub2/grub.cfg),
#     UEFI from the disc (EFI/BOOT/grub.cfg) and UEFI from a USB stick (the copy inside
#     images/efiboot.img, which is also the disc's hidden EFI partition).
# The boot setup is replayed from the original, so the result starts exactly like it.
# Usage: brand-iso.sh <in.iso> <out.iso> <version>     (root, needs xorriso, mtools, cpio)
set -euo pipefail
IN=${1:?in.iso}
OUT=${2:?out.iso}
VERSION=${3:?version}
W=$(mktemp -d)
trap 'umount "$W/iso" 2>/dev/null || true; rm -rf "$W"' EXIT
mkdir -p "$W/iso" "$W/product"
mount -o loop,ro "$IN" "$W/iso"

# 1. product.img with the installer's buildstamp, renamed
unsquashfs -q -n -d "$W/stage2" "$W/iso/images/install.img" .buildstamp
python3 - "$W/stage2/.buildstamp" "$W/product/.buildstamp" "$VERSION" <<'PY'
import configparser, sys
c = configparser.ConfigParser()
c.read(sys.argv[1])
c["Main"]["product"] = "KantanOS"
c["Main"]["version"] = sys.argv[3]
with open(sys.argv[2], "w") as f:
    c.write(f)
PY
(cd "$W/product" && find . | cpio --quiet -o -H newc | gzip -9 > "$W/product.img")

# 2. the boot menus
for cfg in boot/grub2/grub.cfg EFI/BOOT/grub.cfg; do
    mkdir -p "$W/cfg/$(dirname "$cfg")"
    sed -E 's/KantanOS [0-9]+/KantanOS/g' "$W/iso/$cfg" > "$W/cfg/$cfg"
done
cp "$W/iso/images/efiboot.img" "$W/efiboot.img"
chmod u+w "$W/efiboot.img"
mtype -i "$W/efiboot.img" ::/EFI/BOOT/grub.cfg | sed -E 's/KantanOS [0-9]+/KantanOS/g' > "$W/efi-grub.cfg"
mcopy -o -i "$W/efiboot.img" "$W/efi-grub.cfg" ::/EFI/BOOT/grub.cfg
umount "$W/iso"

# 3. a new ISO: same files and boot setup, with the changes
rm -f "$OUT"
xorriso -indev "$IN" -outdev "$OUT" \
    -map "$W/product.img" /images/product.img \
    -map "$W/cfg/boot/grub2/grub.cfg" /boot/grub2/grub.cfg \
    -map "$W/cfg/EFI/BOOT/grub.cfg" /EFI/BOOT/grub.cfg \
    -map "$W/efiboot.img" /images/efiboot.img \
    -boot_image any replay \
    -append_partition 2 28732ac11ff8d211ba4b00a0c93ec93b "$W/efiboot.img" \
    2>&1 | grep -v -E "^xorriso : (UPDATE|NOTE)" | tail -5

# 4. check: the title, and every menu, in the new ISO
mount -o loop,ro "$OUT" "$W/iso"
zcat "$W/iso/images/product.img" | cpio --quiet -i --to-stdout .buildstamp | grep -q "^product = KantanOS"
! grep -q "KantanOS [0-9]" "$W/iso/boot/grub2/grub.cfg" "$W/iso/EFI/BOOT/grub.cfg"
umount "$W/iso"
read -r start size < <(xorriso -indev "$OUT" -report_system_area plain 2>/dev/null |
                        awk '/GPT start and size :   2/ {print $(NF-1), $NF}')
dd if="$OUT" of="$W/part2.img" bs=512 skip="$start" count="$size" status=none
! mtype -i "$W/part2.img" ::/EFI/BOOT/grub.cfg | grep -q "KantanOS [0-9]"
mtype -i "$W/part2.img" ::/EFI/BOOT/grub.cfg | grep -q "Install KantanOS'"
echo "branded: $OUT"
