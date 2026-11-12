#!/bin/bash
# Builds a version and publishes it, signed, to the throwaway test registry.
#   publish-build.sh <version> [disk]     "disk" also makes a fresh VM disk from it
#   publish-build.sh <version> unsigned   pushes WITHOUT a signature (must be refused by PCs)
set -uo pipefail
T="$(cd "$(dirname "$0")/.." && pwd)"
. "$T/update-test/env.sh"
bash "$T/signing/make-key.sh" | tail -1
KANTAN_VERSION="$1" bash "$T/build-image.sh" > /root/build.log 2>&1 || { echo BUILD FAILED; tail -30 /root/build.log; exit 1; }
if [ "${2:-}" = unsigned ]; then
    podman push "$KANTAN_IMAGE:latest" "docker://$KANTAN_IMAGE:latest" 2>&1 | tail -2
else
    bash "$T/publish.sh" 2>&1 | grep -E "^==|Published|rror"
fi
skopeo inspect --tls-verify=false "docker://$KANTAN_IMAGE:latest" | grep -E '"Digest"|"Created"' | head -2
curl -s http://10.0.2.2:5005/v2/kantanos/tags/list; echo
if [ "${2:-}" = disk ]; then bash "$T/vm/export-disk.sh" | tail -2; fi
