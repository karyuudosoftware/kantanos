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
    echo "To test each speaker: System Settings → Sound, then the speaker test for this device."

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

# Connect shares from a NAS so they work like normal folders in every app
kantan-nas-connect:
    #!/usr/bin/bash
    sudo /usr/libexec/kantanos/nas-connect

# Show the NAS shares that are connected
kantan-nas-list:
    #!/usr/bin/bash
    /usr/libexec/kantanos/nas-connect list

# Disconnect all NAS shares set up with kantan-nas-connect
kantan-nas-remove:
    #!/usr/bin/bash
    sudo /usr/libexec/kantanos/nas-connect remove

# What another device needs to wake this PC over the network (Wake-on-LAN)
kantan-wake-info:
    #!/usr/bin/bash
    found=0
    for dev in $(nmcli -t -f DEVICE,TYPE device | awk -F: '$2=="ethernet"{print $1}'); do
        found=1
        mac=$(cat "/sys/class/net/$dev/address")
        wol=$(nmcli -g 802-3-ethernet.wake-on-lan connection show "$(nmcli -g GENERAL.CONNECTION device show "$dev")" 2>/dev/null)
        ip=$(nmcli -g IP4.ADDRESS device show "$dev" | head -n1)
        echo "Network port $dev"
        echo "  MAC address (enter this in your wake-up app): $mac"
        echo "  IP address on your network: ${ip:-not connected}"
        echo "  Wake-on-LAN: ${wol:-default (on)}"
    done
    [ "$found" = 1 ] || { echo "No wired network port found. Wake-on-LAN needs a network cable."; exit 1; }
    echo
    echo "Also needed, once, in the BIOS: turn on \"Wake on LAN\" (sometimes \"Power On By PCI-E\")"
    echo "and turn off \"ErP\", or the network port has no power while the PC is off."

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

# Show the screens and where the dock and top bar are (helps when the dock is missing)
kantan-display-info:
    #!/usr/bin/bash
    /usr/libexec/kantanos/dock-repair info

# Put the KantanOS Dock back (keeps its apps)
kantan-reset-dock:
    #!/usr/bin/bash
    /usr/libexec/kantanos/dock-repair reset

# Choose the main screen (the dock, top bar and login screen go there). An AV receiver
# connected by HDMI can count as a screen of its own.
kantan-main-screen OUTPUT="":
    #!/usr/bin/bash
    source /usr/lib/ujust/ujust.sh
    out="{{ OUTPUT }}"
    if [ -z "$out" ]; then
        mapfile -t rows < <(kscreen-doctor -j | jq -r '.outputs[] | select(.connected) |
            "\(.name)  (\(if .enabled then "on" else "off" end), priority \(.priority // "-"), \(.size.width // 0)x\(.size.height // 0))"')
        [ "${#rows[@]}" -gt 0 ] || { echo "No screens found."; exit 1; }
        echo "Which screen is your TV or monitor?"
        choice=$(Choose "${rows[@]}")
        out=${choice%% *}
    fi
    kscreen-doctor "output.$out.enable" "output.$out.priority.1" && echo "$out is now the main screen."
    ujust kantan-login-screen-sync

# Make the login screen use the same screen layout as your desktop
kantan-login-screen-sync:
    #!/usr/bin/bash
    cfg="$HOME/.config/kwinoutputconfig.json"
    [ -f "$cfg" ] || { echo "No screen layout saved yet: change something in System Settings → Display first."; exit 1; }
    sudo install -d -o plasmalogin -g plasmalogin -m 0755 /var/lib/plasmalogin/.config
    sudo install -o plasmalogin -g plasmalogin -m 0644 "$cfg" /var/lib/plasmalogin/.config/kwinoutputconfig.json
    echo "Done. The login screen uses your screen layout from the next restart."

# Stop (off) or restore (on) the admin password prompts for your account
kantan-admin-password STATE="status":
    #!/usr/bin/bash
    rules=/etc/polkit-1/rules.d/40-kantanos-no-admin-password.rules
    sudoers=/etc/sudoers.d/40-kantanos-no-admin-password
    case "{{ STATE }}" in
        off)
            id -nG | grep -qw wheel || { echo "Only an administrator account can do this."; exit 1; }
            echo "After this, $USER is never asked for the password for system changes, and"
            echo "neither is any program $USER runs. Other accounts still are."
            read -r -p "Turn admin password prompts off for $USER? [y/N] " ok
            [ "${ok,,}" = y ] || exit 0
            printf '%s\n' "// KantanOS: no admin password prompts for $USER (ujust kantan-admin-password on undoes this)" \
                "polkit.addRule(function(action, subject) {" \
                "    if (subject.user == \"$USER\" && subject.local && subject.active) return polkit.Result.YES;" \
                "});" | sudo tee "$rules" >/dev/null
            tmp=$(mktemp); echo "$USER ALL=(ALL) NOPASSWD: ALL" > "$tmp"
            if sudo visudo -cf "$tmp" >/dev/null; then sudo install -m 0440 "$tmp" "$sudoers"; fi
            rm -f "$tmp"
            echo "Done: no more admin password prompts for $USER."
            ;;
        on)
            sudo rm -f "$rules" "$sudoers"
            echo "Done: system changes ask for the admin password again."
            ;;
        *)
            if [ -e "$rules" ]; then echo "Admin password prompts are OFF ($(grep -o 'user == "[^"]*"' "$rules"))."
            else echo "Admin password prompts are on (the normal setting)."; fi
            echo "Change with: ujust kantan-admin-password off   or   ujust kantan-admin-password on"
            ;;
    esac

# Bigger or smaller text in Android apps (Waydroid): small, medium, large (default) or huge
kantan-waydroid-text-size SIZE="large":
    #!/usr/bin/bash
    case "{{ SIZE }}" in
        small) dpi=160 ;; medium) dpi=213 ;; large) dpi=280 ;; huge) dpi=360 ;;
        [0-9]*) dpi="{{ SIZE }}" ;;
        *) echo "Use small, medium, large or huge."; exit 2 ;;
    esac
    prop=/var/lib/waydroid/waydroid_base.prop
    sudo test -f "$prop" || { echo "Set up Android apps first: ujust setup-waydroid"; exit 1; }
    sudo sed -i '/^ro.sf.lcd_density=/d' "$prop"
    echo "ro.sf.lcd_density=$dpi" | sudo tee -a "$prop" >/dev/null
    waydroid session stop 2>/dev/null || true
    sudo systemctl restart waydroid-container
    echo "Android text size set to {{ SIZE }} ($dpi). Open Waydroid again to see it."

# Set this PC's location by town name (for weather and clocks); "clear" goes back to automatic
kantan-set-location PLACE="":
    #!/usr/bin/bash
    place="{{ PLACE }}"
    if [ "$place" = clear ]; then
        sudo rm -f /etc/geolocation && sudo systemctl restart geoclue 2>/dev/null
        echo "Location is found automatically again."; exit 0
    fi
    [ -n "$place" ] || read -r -p "Your town or city (for example: Toronto, Canada): " place
    [ -n "$place" ] || exit 1
    # OpenStreetMap's place search; only the town name you typed is sent
    hit=$(curl -fsS -G -A "KantanOS-location-setup" --data-urlencode "q=$place" \
          -d format=json -d limit=1 https://nominatim.openstreetmap.org/search \
          | jq -r '.[0] | select(.) | "\(.lat) \(.lon) \(.display_name)"')
    [ -n "$hit" ] || { echo "Couldn't find \"$place\". Try adding the country."; exit 1; }
    read -r lat lon name <<< "$hit"
    echo "Found: $name"
    read -r -p "Use this as the PC's location? [Y/n] " ok
    [ "${ok,,}" = n ] && exit 0
    printf '# KantanOS: fixed location for this PC (ujust kantan-set-location)\n%s\n%s\n0\n1000\n' "$lat" "$lon" \
        | sudo tee /etc/geolocation >/dev/null
    sudo chmod 0644 /etc/geolocation
    sudo systemctl restart geoclue 2>/dev/null || true
    echo "Done. Weather apps use this location from now on (restart any that are open)."

# Block bad sites: "status" (what is blocked), "update" (fetch the list now) or "window" (settings)
kantan-block-sites ACTION="status":
    #!/usr/bin/bash
    case "{{ ACTION }}" in
        update) sudo /usr/libexec/kantanos/site-blocker-apply update --force >/dev/null && echo "The list is up to date." ;;
        window) nohup setsid /usr/libexec/kantanos/site-blocker >/dev/null 2>&1 & ;;
        *)
            /usr/libexec/kantanos/site-blocker-apply status | jq -r '
                "Blocking sites on the list: \(if .settings.on then "on" else "off" end)",
                "Sites on the list: \(.state.listed // 0), blocked now: \(.state.blocked // 0)",
                "Kinds turned off: \([.settings.categories | to_entries[] | select(.value | not) | .key] | join(", ") | if . == "" then "none" else . end)",
                "Always allowed: \(.settings.allow | join(", ") | if . == "" then "none" else . end)",
                "Safe look-up service (Quad9): \(if .settings.safe_dns then "on" else "off" end)"'
            echo "Change these in Welcome → Tools → Block bad sites, or: ujust kantan-block-sites window"
            ;;
    esac

# Firewall: "strict" (KantanOS, the normal setting) or "open" (Fedora's, every port above 1024)
kantan-firewall STATE="status":
    #!/usr/bin/bash
    case "{{ STATE }}" in
        strict) sudo firewall-cmd --set-default-zone=KantanOS && echo "Firewall: KantanOS (strict)." ;;
        open)
            echo "This lets other devices on your network connect to any program on this PC that listens."
            read -r -p "Open the firewall? [y/N] " ok
            [ "${ok,,}" = y ] && sudo firewall-cmd --set-default-zone=FedoraWorkstation && echo "Firewall: open. Undo with: ujust kantan-firewall strict"
            ;;
        *)
            zone=$(firewall-cmd --get-default-zone 2>/dev/null)
            echo "Firewall zone: $zone"
            [ "$zone" = KantanOS ] && echo "Strict: only phone link, game streaming, device discovery and file sharing can be reached from the network."
            echo "Change with: ujust kantan-firewall strict   or   ujust kantan-firewall open"
            ;;
    esac
