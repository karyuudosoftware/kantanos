#!/bin/bash
# Builds the KantanOS container image. Run as root inside the Fedora build environment.
# The image is always tagged localhost/kantanos:latest; when an update address is set
# (tools/registry.conf or the KANTAN_IMAGE variable) it is tagged with that name as well.
set -euo pipefail
cd "$(dirname "$0")/.."
. tools/image-ref.sh
VERSION=${KANTAN_VERSION:-$(cat VERSION)}
BUILD=${KANTAN_BUILD:-$(date -u +%Y%m%d)}
python3 tools/looks.py >/dev/null            # looks first: the renderer uses what it writes
bash tools/render-branding.sh >/dev/null
python3 tools/make-plasma-theme.py >/dev/null
python3 tools/make-welcome.py >/dev/null
python3 tools/make-file-manager.py >/dev/null
TAGS=(-t localhost/kantanos:latest -t "localhost/kantanos:$VERSION")
[ -n "$KANTAN_IMAGE" ] && TAGS+=(-t "$KANTAN_IMAGE:latest")
podman build \
    --build-arg KANTAN_VERSION="$VERSION" \
    --build-arg KANTAN_BUILD="$BUILD" \
    --build-arg KANTAN_IMAGE="$KANTAN_IMAGE" \
    "${TAGS[@]}" \
    -f Containerfile .
podman images | grep kantanos
