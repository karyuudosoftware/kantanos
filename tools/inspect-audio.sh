#!/bin/bash
# Audio stack in the image: PipeWire/WirePlumber versions, config folders, suspend settings, test tools.
podman run --rm --entrypoint bash localhost/kantanos:latest -c '
rpm -q pipewire wireplumber alsa-utils pipewire-utils 2>&1
echo "== wireplumber conf dirs"; ls -d /usr/share/wireplumber/wireplumber.conf.d /etc/wireplumber/wireplumber.conf.d 2>&1
ls /usr/share/wireplumber/wireplumber.conf.d/ 2>/dev/null
echo "== suspend timeout mentions"; grep -rn "suspend-timeout\|suspend.timeout\|dither.noise" /usr/share/wireplumber /usr/share/pipewire 2>/dev/null | head -12
echo "== existing alsa rules in drop-ins"; grep -rln "monitor.alsa.rules" /usr/share/wireplumber/wireplumber.conf.d /etc/wireplumber 2>/dev/null
echo "== test tools"; command -v speaker-test pw-play pw-cat wpctl paplay
ls /usr/share/sounds/alsa 2>/dev/null | head
'
