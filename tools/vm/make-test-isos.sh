#!/bin/bash
# Makes two small UDF disc images shaped like Windows install discs, for testing the Windows
# VM setup without a real Windows ISO: sources/lang.ini plus an install.wim that holds only
# the WIM header and its edition list (no Windows in it). Run as root in the build distro
# (needs mkudffs from udftools and a loop mount).
#   output/test-isos/win11-consumer.iso   en-US, Home + Pro (+ others), build 26100
#   output/test-isos/win10-iot-ltsc.iso   ja-JP, IoT Enterprise LTSC 2021, build 19044
set -euo pipefail
OUT=/mnt/d/CLAUDE_Projects/kantanos/output/test-isos
mkdir -p "$OUT"

make_disc() {   # name lang editions-spec...
    local name=$1 lang=$2; shift 2
    local work; work=$(mktemp -d)
    mkdir -p "$work/sources"
    printf '[Available UI Languages]\r\n%s = 3\r\n[Fallback Languages]\r\n%s = en-us\r\n' "$lang" "$lang" > "$work/sources/lang.ini"
    python3 - "$work/sources/install.wim" "$@" <<'PY'
import struct, sys
path, specs = sys.argv[1], sys.argv[2:]
images = []
for i, spec in enumerate(specs, 1):
    edition, build, name = spec.split(":", 2)
    images.append(f'<IMAGE INDEX="{i}"><WINDOWS><EDITIONID>{edition}</EDITIONID>'
                  f'<VERSION><MAJOR>10</MAJOR><MINOR>0</MINOR><BUILD>{build}</BUILD></VERSION></WINDOWS>'
                  f'<NAME>{name}</NAME><DISPLAYNAME>{name}</DISPLAYNAME></IMAGE>')
xml = b"\xff\xfe" + ("<WIM>" + "".join(images) + "</WIM>").encode("utf-16-le")   # UTF-16 with BOM, as in real WIMs
offset = 4096
head = bytearray(208)
head[0:8] = b"MSWIM\0\0\0"
struct.pack_into("<I", head, 8, 208)
struct.pack_into("<I", head, 44, len(specs))
head[72:79] = len(xml).to_bytes(7, "little")      # XML resource: size, flags, offset, original size
head[79] = 0x02                                    # metadata flag only (not compressed)
head[80:88] = offset.to_bytes(8, "little")
head[88:96] = len(xml).to_bytes(8, "little")
with open(path, "wb") as f:
    f.write(head)
    f.write(b"\0" * (offset - len(head)))
    f.write(xml)
PY
    local img="$OUT/$name.iso"
    rm -f "$img"
    truncate -s 8M "$img"
    mkudffs --media-type=hd --label="TEST_$lang" "$img" >/dev/null
    local mnt; mnt=$(mktemp -d)
    mount -o loop "$img" "$mnt"
    cp -r "$work/sources" "$mnt/"
    umount "$mnt"
    rmdir "$mnt"; rm -rf "$work"
    echo "made $img"
}

make_disc win11-consumer en-us \
    "Core:26100:Windows 11 Home" "Education:26100:Windows 11 Education" \
    "Professional:26100:Windows 11 Pro" "ProfessionalWorkstation:26100:Windows 11 Pro for Workstations"
make_disc win10-iot-ltsc ja-jp "IoTEnterpriseS:19044:Windows 10 IoT Enterprise LTSC 2021"
