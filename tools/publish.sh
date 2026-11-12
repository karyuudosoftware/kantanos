#!/bin/bash
# Signs the built image and pushes it to the update address (tools/registry.conf).
# Installed PCs only accept images signed with this key.
#   publish.sh [private-key-file]      default: signing/cosign.key
# Log in to the registry first (podman login) when it needs it.
set -euo pipefail
cd "$(dirname "$0")/.."
. tools/image-ref.sh
[ -n "$KANTAN_IMAGE" ] || { echo "No update address set in tools/registry.conf"; exit 1; }
KEY=${1:-signing/cosign.key}
[ -f "$KEY" ] || { echo "Signing key $KEY not found (tools/signing/make-key.sh creates one)"; exit 1; }

# Store signatures next to the image in the registry.
mkdir -p /etc/containers/registries.d
printf 'docker:\n  %s:\n    use-sigstore-attachments: true\n' "$KANTAN_IMAGE" \
    > /etc/containers/registries.d/kantanos.yaml

VERSION=$(podman run --rm --entrypoint bash "$KANTAN_IMAGE:latest" -c '. /usr/lib/os-release; echo "$KANTAN_VERSION"')
BUILD=$(podman run --rm --entrypoint bash "$KANTAN_IMAGE:latest" -c '. /usr/lib/os-release; echo "$KANTAN_BUILD"')
PASS=$(mktemp); trap 'rm -f "$PASS"' EXIT   # the key has an empty passphrase
for tag in "$VERSION-$BUILD" "$VERSION" latest; do
    echo "== pushing $KANTAN_IMAGE:$tag"
    podman push --sign-by-sigstore-private-key "$KEY" --sign-passphrase-file "$PASS" \
        "$KANTAN_IMAGE:latest" "docker://$KANTAN_IMAGE:$tag"
done
echo "Published $KANTAN_IMAGE ($VERSION, build $BUILD)"
