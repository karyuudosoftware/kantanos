#!/bin/bash
# Creates the KantanOS image signing key pair (once).
#   signing/cosign.key   private key: keep it safe, never commit it (it is in .gitignore)
#   system_files/etc/pki/containers/kantanos.pub   public key: built into every image
# Run as root inside the Fedora build environment.
set -euo pipefail
cd "$(dirname "$0")/../.."
mkdir -p signing system_files/etc/pki/containers
if [ -f signing/cosign.key ]; then echo "signing/cosign.key already exists; not replacing it"; exit 0; fi
W=$(mktemp -d)
# cosign ships in the base image, so borrow it from there.
podman run --rm -e COSIGN_PASSWORD= -v "$W":/w:Z -w /w --entrypoint cosign \
    localhost/kantanos:latest generate-key-pair
cp "$W/cosign.key" signing/cosign.key
cp "$W/cosign.pub" signing/cosign.pub
cp "$W/cosign.pub" system_files/etc/pki/containers/kantanos.pub
rm -rf "$W"
ls -la signing system_files/etc/pki/containers
