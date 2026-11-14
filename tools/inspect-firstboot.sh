#!/bin/bash
# Shows the base's login display unit and what its first-boot hardware setup changes.
podman run --rm --entrypoint bash localhost/kantanos:latest -c '
echo "== plasma-login-kwin_wayland.service"; cat /usr/lib/systemd/user/plasma-login-kwin_wayland.service
echo "== session kwin timeouts"; grep -n -i "Timeout" /usr/lib/systemd/user/plasma-kwin_wayland.service /usr/lib/systemd/user/plasma-login*.service 2>/dev/null
echo "== hardware setup: kernel arguments it may add"; grep -n -i -E "NEEDED_KARGS|append-if-missing|ertm|karg" /usr/libexec/bazzite-hardware-setup | head -40
'
