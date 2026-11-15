#!/bin/bash
# Which panel-background element prefixes the panel uses (per edge, floating, etc.).
podman run --rm --entrypoint bash localhost/kantanos:latest -c '
F=$(find /usr/lib64 -path "*plasma/applets/org.kde.panel.so" 2>/dev/null | head -1)
echo "panel plugin: $F"
{ strings "$F"; strings -el "$F"; } | grep -E "prefix|north|south|floating|panel-background|enabledBorders" | grep -v "^_Z" | head -40
echo "== plasmashell lib"
L=$(ls /usr/lib64/libPlasmaQuick.so* 2>/dev/null | head -1); echo "$L"
{ strings "$L"; strings -el "$L"; } | grep -E "\b(north|south|floating)\b|panel-background" | head -20
'
