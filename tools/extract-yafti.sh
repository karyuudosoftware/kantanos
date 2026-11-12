#!/bin/bash
# Copies Bazzite Portal's config and launcher out of the image for reference.
OUT=/mnt/d/CLAUDE_Projects/kantanos/output/yafti-ref
mkdir -p "$OUT"
podman run --rm --entrypoint bash -v "$OUT":/out localhost/kantanos:latest -c '
cp /usr/share/yafti/yafti.yml /out/; cp /usr/bin/yafti_gtk.py /out/; cp /usr/share/applications/io.github.ublue_os.yafti_gtk.desktop /out/ 2>/dev/null
echo "== flatpak patterns"; grep -n -i "flatpak" /usr/share/yafti/yafti.yml | head -20
echo "== screen titles"; grep -n -E "^  - title:" /usr/share/yafti/yafti.yml
echo "== autostart logic"; grep -n -i -E "autostart|\.desktop|startup" /usr/bin/yafti_gtk.py | head -30
echo "== keys used"; grep -o -E "\.get\(\"[a-z_]+\"" /usr/bin/yafti_gtk.py | sort | uniq -c
'
