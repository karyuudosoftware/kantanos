#!/bin/bash
# Shows how the base image handles updates and image signature policy.
podman run --rm localhost/kantanos:latest bash -c '
echo "== policy.json"; cat /etc/containers/policy.json
echo "== registries.d"; ls /etc/containers/registries.d/; cat /etc/containers/registries.d/*.yaml 2>/dev/null | head -40
echo "== pki"; ls -R /etc/pki/containers 2>/dev/null
echo "== update units"; systemctl list-unit-files 2>/dev/null | grep -Ei "uupd|rpm-ostreed-automatic|bootc-fetch|ublue-update|topgrade"
echo "== uupd"; command -v uupd; ls /etc/uupd* /usr/share/uupd* 2>/dev/null; cat /etc/uupd/config.json 2>/dev/null
echo "== timer"; cat /usr/lib/systemd/system/uupd.timer 2>/dev/null
echo "== service"; cat /usr/lib/systemd/system/uupd.service 2>/dev/null
echo "== image-info"; cat /usr/share/ublue-os/image-info.json 2>/dev/null
echo "== just update"; grep -rn "^update\|^rebase\|^rollback" /usr/share/ublue-os/just/*.just 2>/dev/null | head -20
echo "== tools"; command -v cosign skopeo bootc rpm-ostree brh bazzite-rollback-helper
'
echo "== host tools"; command -v cosign skopeo; podman images --format "{{.Repository}}:{{.Tag}} {{.Size}}" | head
