#!/bin/bash
# Checks the published image: reachable without a login, tagged, and signed with the KantanOS key.
. "$(dirname "$0")/image-ref.sh"
echo "== anonymous access to $KANTAN_IMAGE"
skopeo inspect --no-creds "docker://$KANTAN_IMAGE:latest" 2>&1 | grep -E '"Digest"|"Created"|rror|denied|unauthorized' | head -3
echo "== tags"
skopeo list-tags --no-creds "docker://$KANTAN_IMAGE" 2>&1 | tr -d '\n ' | cut -c1-400; echo
echo "== signature check with the key built into the image"
podman run --rm --entrypoint cosign localhost/kantanos:latest verify \
    --key /etc/pki/containers/kantanos.pub --insecure-ignore-tlog=true \
    "$KANTAN_IMAGE:latest" 2>&1 | grep -v '^\[{' | tail -6
