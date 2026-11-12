#!/bin/bash
# Removes the throwaway test registry and the test-address image tags.
podman rm -f kantan-registry 2>/dev/null
rm -rf /root/kantan-registry
rm -f /etc/containers/registries.conf.d/99-kantan-test.conf /etc/containers/registries.d/kantanos.yaml
podman images --format '{{.Repository}}:{{.Tag}}' | grep '^10.0.2.2:5005/' | xargs -r podman rmi
podman rmi docker.io/library/registry:2 2>/dev/null
podman image prune -f >/dev/null
podman images --format '{{.Repository}}:{{.Tag}} {{.Size}}'
df -h /root | tail -1
