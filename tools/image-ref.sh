# Sourced by the build scripts. Sets KANTAN_IMAGE (the published address, may be empty)
# and LOCAL_IMAGE (the name the image has in local storage).
# An already-set KANTAN_IMAGE environment variable wins over tools/registry.conf.
if [ -z "${KANTAN_IMAGE:-}" ]; then
    . "$(dirname "${BASH_SOURCE[0]}")/registry.conf"
fi
KANTAN_IMAGE="${KANTAN_IMAGE:-}"
LOCAL_IMAGE="${KANTAN_IMAGE:-localhost/kantanos}"
export KANTAN_IMAGE LOCAL_IMAGE
