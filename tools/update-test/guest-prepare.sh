# Runs inside the test VM: let it reach the throwaway test registry over plain HTTP
# (test only; real PCs use the real registry over HTTPS), then show the update state.
mkdir -p /etc/containers/registries.conf.d
cat > /etc/containers/registries.conf.d/99-kantan-test.conf <<'CONF'
[[registry]]
location = "10.0.2.2:5005"
insecure = true
CONF
echo "== version"; grep -E "^(PRETTY_NAME|KANTAN_)" /usr/lib/os-release
echo "== booted image"; bootc status 2>&1 | head -14
echo "== policy for our address"; jq -c '.transports.docker["10.0.2.2:5005/kantanos"]' /etc/containers/policy.json
echo "== timer"; systemctl is-enabled uupd.timer; systemctl list-timers uupd.timer --no-pager | sed -n 2p
echo "== registry reachable"; curl -s -m 10 http://10.0.2.2:5005/v2/kantanos/tags/list; echo
