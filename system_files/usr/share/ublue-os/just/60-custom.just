# KantanOS helper commands. Run with: ujust <name>

# Turn HDR and wide colour on for every connected display that supports it
kantan-hdr-on:
    #!/usr/bin/bash
    for o in $(kscreen-doctor -j | jq -r '.outputs[] | select(.connected and .enabled) | .name'); do
        echo "Enabling HDR on $o"
        kscreen-doctor "output.$o.hdr.enable" "output.$o.wcg.enable" || echo "  $o does not support HDR"
    done

# Turn HDR off again on every display
kantan-hdr-off:
    #!/usr/bin/bash
    for o in $(kscreen-doctor -j | jq -r '.outputs[] | select(.connected and .enabled) | .name'); do
        kscreen-doctor "output.$o.hdr.disable" "output.$o.wcg.disable" || true
    done

# Switch the HDMI audio output to 7.1 surround (for an AV receiver)
kantan-audio-71:
    #!/usr/bin/bash
    found=0
    while read -r card profile; do
        [ -z "$card" ] && continue
        echo "Setting $card to $profile"
        pactl set-card-profile "$card" "$profile" && found=1 && break
    done < <(pactl -f json list cards | jq -r '.[] | .name as $c | .profiles | to_entries[] | select(.key | test("hdmi-surround71")) | select(.value.available != false) | "\($c) \(.key)"')
    if [ "$found" = 0 ]; then
        echo "No HDMI device offering 7.1 was found. Turn the receiver on first, then run this again."
        exit 1
    fi
    echo "Done. Test each speaker with: ujust kantan-speaker-test"

# Say each speaker's name from that speaker, one at a time ("Front Left", "Side Right", ...)
kantan-speaker-test:
    #!/usr/bin/bash
    sink="$(pactl get-default-sink)"
    ch="$(pactl -f json list sinks | jq -r --arg s "$sink" '.[] | select(.name == $s) | .sample_specification' | grep -o '[0-9]ch' | tr -dc '0-9')"
    ch="${ch:-8}"
    echo "Output: $sink ($ch channels)"
    echo "Each speaker says its own name. If a name comes from the wrong speaker, or from"
    echo "two speakers at once, note which; then check the receiver's listening mode."
    speaker-test -D pipewire -c "$ch" -t wav -l 1 2>&1 | grep -E "^ ?[0-9] - " || true

# Keep HDMI audio awake so an AV receiver never misses the start of a sound (on by default)
kantan-hdmi-keepalive STATE="status":
    #!/usr/bin/bash
    f="${XDG_CONFIG_HOME:-$HOME/.config}/wireplumber/wireplumber.conf.d/61-kantanos-hdmi-keepalive-off.conf"
    case "{{STATE}}" in
        off)
            mkdir -p "$(dirname "$f")"
            printf 'monitor.alsa.rules = [\n  {\n    matches = [\n      { node.name = "~alsa_output.*hdmi.*" }\n      { node.name = "~alsa_output.*HDMI.*" }\n      { node.name = "~alsa_output.*displayport.*" }\n    ]\n    actions = { update-props = { session.suspend-timeout-seconds = 5, dither.noise = 0 } }\n  }\n]\n' > "$f"
            systemctl --user restart wireplumber && echo "HDMI keep-awake is off." ;;
        on)
            rm -f "$f"; systemctl --user restart wireplumber && echo "HDMI keep-awake is on." ;;
        *)
            [ -f "$f" ] && echo "HDMI keep-awake: off" || echo "HDMI keep-awake: on"
            wpctl status 2>/dev/null | sed -n '/Sinks:/,/Sources:/p' | head -8 ;;
    esac

# Show the KantanOS version and the Bazzite base it was built from
kantan-version:
    #!/usr/bin/bash
    . /usr/lib/os-release
    echo "$PRETTY_NAME — build: $KANTAN_BUILD — edition: $KANTAN_EDITION — base: Bazzite $OSTREE_VERSION"
    echo "Updates from: ${KANTAN_IMAGE:-(no update address in this build)}"

# Check for a KantanOS update now and install it (it takes effect at the next restart)
kantan-update:
    #!/usr/bin/bash
    sudo bootc upgrade && echo "Restart the PC to finish, or carry on and restart later."

# Go back to the version that was running before the last update (takes effect at the next restart)
kantan-undo-update:
    #!/usr/bin/bash
    sudo bootc rollback && echo "Restart the PC to return to the previous version."
