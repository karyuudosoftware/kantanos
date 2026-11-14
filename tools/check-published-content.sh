#!/bin/bash
# Pulls the published image (only layers that differ from local ones are downloaded) and
# runs the static checks against exactly what installed PCs will receive.
. "$(dirname "$0")/image-ref.sh"
podman pull -q "$KANTAN_IMAGE:latest" >/dev/null || exit 1
podman run --rm --entrypoint bash "$KANTAN_IMAGE:latest" -c 'grep -E "^KANTAN_(VERSION|BUILD)" /usr/lib/os-release'
bash "$(dirname "$0")/verify-image.sh" "$KANTAN_IMAGE:latest" | grep -E "FAIL|file manager|sidebar"
echo "checks finished"
