# Update test settings. A throwaway registry runs in the build environment; the test VM
# reaches it as 10.0.2.2:5005 (QEMU's name for the host), so the build environment gets
# the same address on its loopback and images are signed for exactly that name.
export KANTAN_IMAGE=10.0.2.2:5005/kantanos
ip addr show dev lo | grep -q '10.0.2.2/32' || ip addr add 10.0.2.2/32 dev lo
mkdir -p /etc/containers/registries.conf.d
cat > /etc/containers/registries.conf.d/99-kantan-test.conf <<'CONF'
[[registry]]
location = "10.0.2.2:5005"
insecure = true
CONF
if ! podman container exists kantan-registry; then
    mkdir -p /root/kantan-registry
    podman run -d --name kantan-registry -p 5005:5000 \
        -v /root/kantan-registry:/var/lib/registry docker.io/library/registry:2
fi
podman start kantan-registry >/dev/null
