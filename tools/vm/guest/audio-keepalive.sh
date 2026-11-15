# Runs as the test user in the VM (which has an emulated analog sound card, not HDMI):
# applies the KantanOS keep-awake rule to that card, then checks the output stays running
# when nothing plays. Before: the output suspends after 5 s of silence.
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
state() { pactl -f json list sinks | jq -r '.[] | select(.name | test("alsa_output")) | "\(.name)  \(.state)"'; }
D=~/.config/wireplumber/wireplumber.conf.d
rm -f $D/99-test-keepalive.conf; systemctl --user restart wireplumber; sleep 4
paplay /usr/share/sounds/alsa/Front_Center.wav; sleep 12
echo "== without the rule, 12 s after a sound:"; state
mkdir -p $D
sed 's/hdmi\.\*" }/hdmi.*" }\n      { node.name = "~alsa_output.*analog.*" }/' /usr/share/wireplumber/wireplumber.conf.d/60-kantanos-hdmi-keepalive.conf > $D/99-test-keepalive.conf
systemctl --user restart wireplumber; sleep 4
paplay /usr/share/sounds/alsa/Front_Center.wav; sleep 12
echo "== with the rule, 12 s after a sound:"; state
id=$(wpctl status | sed -n '/Sinks:/,/Sources:/p' | grep -o '[0-9]\+\.' | head -1 | tr -d .)
wpctl inspect "$id" | grep -E "suspend-timeout|dither.noise"
journalctl --user -u wireplumber -b --no-pager -o cat | grep -i -E "error|parse|syntax" | tail -3
rm -f $D/99-test-keepalive.conf; systemctl --user restart wireplumber
