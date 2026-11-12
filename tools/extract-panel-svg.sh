#!/bin/bash
# Copies Breeze's panel background SVGs out of the image so a KantanOS variant can be derived.
OUT=/mnt/d/CLAUDE_Projects/kantanos/output/breeze-ref
mkdir -p "$OUT"
podman run --rm --entrypoint bash -v "$OUT":/out localhost/kantanos:latest -c '
T=/usr/share/plasma/desktoptheme/default
zcat $T/widgets/panel-background.svgz > /out/panel-background.svg
zcat $T/translucent/widgets/panel-background.svgz > /out/panel-background-translucent.svg
zcat $T/opaque/widgets/panel-background.svgz > /out/panel-background-opaque.svg
zcat $T/translucent/dialogs/background.svgz > /out/dialog-background-translucent.svg 2>/dev/null
cat $T/metadata.json > /out/metadata.json; cat $T/plasmarc > /out/plasmarc 2>/dev/null
ls $T $T/translucent $T/translucent/widgets $T/translucent/dialogs 2>/dev/null
echo "== ids"; grep -o "id=\"[^\"]*\"" /out/panel-background-translucent.svg | sort -u | tr "\n" " "
echo; wc -c /out/*.svg
'
