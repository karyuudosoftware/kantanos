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
    echo "Done. Test the speakers in System Settings > Sound."

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
