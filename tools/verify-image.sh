#!/bin/bash
# Static checks on the built image (no VM needed).
IMG=${1:-localhost/kantanos:latest}
podman run --rm --entrypoint bash "$IMG" -c '
fail=0
check() { if eval "$2" >/dev/null 2>&1; then echo "PASS  $1"; else echo "FAIL  $1"; fail=1; fi; }
K=$(ls /usr/lib/modules | head -n1)
I=/usr/lib/modules/$K/initramfs.img
echo "initramfs: $(du -h $I | cut -f1)"
check "os-release says KantanOS"            "grep -q \"^NAME=\\\"KantanOS\\\"\" /usr/lib/os-release"
check "os-release ID still bazzite"         "grep -q ^ID=bazzite /usr/lib/os-release"
check "default look is org.kantanos"        "grep -q LookAndFeelPackage=org.kantanos.desktop /etc/xdg/kdeglobals"
check "look-and-feel layout present"        "test -f /usr/share/plasma/look-and-feel/org.kantanos.desktop/contents/layouts/org.kde.plasma.desktop-layout.js"
check "colour schemes for every look"       "for l in \$(cat /usr/share/kantanos/looks/order); do test -s /usr/share/color-schemes/Kantan\${l^}.colors && test -s /usr/share/kantanos/looks/\$l/wallpaper.png && test -s /usr/share/kantanos/looks/\$l/logo.png || exit 1; done"
check "default look is Light"               "grep -q ColorScheme=KantanLight /usr/share/plasma/look-and-feel/org.kantanos.desktop/contents/defaults && test \"\$(HOME=/tmp/fmtest kantan-look current)\" = light"
check "wallpaper present"                   "test -s /usr/share/wallpapers/KantanOS/contents/images/3840x2160.png"
check "launcher icon present"               "test -s /usr/share/icons/hicolor/64x64/apps/kantanos.png"
check "plymouth default is kantanos"        "test \"\$(plymouth-set-default-theme)\" = kantanos"
check "initramfs is a valid image"          "lsinitrd $I | grep -q systemd"
check "initramfs has ostree"                "lsinitrd $I | grep -q ostree-prepare-root"
check "initramfs has kantanos splash"       "lsinitrd $I | grep -q themes/kantanos/watermark.png"
check "fcitx5 + mozc installed"             "rpm -q fcitx5 fcitx5-mozc"
check "fcitx5 wayland launcher exists"      "test -f /usr/share/applications/fcitx5-wayland-launcher.desktop"
check "Japanese locale installed"           "locale -a | grep -q -i ja_JP.utf8"
check "Inter font installed"                "fc-list | grep -q -i \"Inter Variable\""
check "mpv installed"                       "rpm -q mpv"
check "ffmpeg has h264/hevc/av1 decoders"   "ffmpeg -hide_banner -decoders | grep -E -q \" hevc \" && ffmpeg -hide_banner -decoders | grep -q \" h264 \" && ffmpeg -hide_banner -decoders | grep -q av1"
check "ffmpeg has ac3/eac3/dts/truehd"      "for c in ac3 eac3 dca truehd; do ffmpeg -hide_banner -decoders | grep -q \" \$c \" || exit 1; done"
check "ujust recipes parse"                 "just --justfile /usr/share/ublue-os/justfile --list | grep -q kantan-hdr-on"
check "lock/login wallpaper is KantanOS"     "grep -q wallpapers/KantanOS /etc/xdg/kscreenlockerrc"
check "boot splash kernel args set"         "grep -q rhgb /usr/lib/bootc/kargs.d/10-kantanos.toml"
check "login screen wallpaper is KantanOS"   "grep -q wallpapers/KantanOS /usr/lib/plasmalogin/defaults.conf"
check "no Bazzite announcements autostart"  "test ! -e /etc/xdg/autostart/bazzite-announcement.desktop"
check "welcome autostart is KantanOS"       "grep -q KantanOS /etc/skel/.config/autostart/bazzite-portal.desktop"
check "glass panel theme present"           "test -s /usr/share/plasma/desktoptheme/KantanGlass/translucent/widgets/panel-background.svg"
check "starter-app service enabled"         "systemctl is-enabled kantanos-flatpak-setup.service"
check "starter-app script executable"       "test -x /usr/libexec/kantanos/flatpak-setup"
check "Steam does not autostart"            "test ! -e /etc/skel/.config/autostart/steam.desktop"
check "welcome app is KantanOS"             "grep -q KantanOS /usr/share/yafti/yafti.yml && grep -q KantanOS /usr/bin/yafti_gtk.py && ! grep -q -i bazzite /usr/share/yafti/yafti.yml"
check "welcome definition is valid YAML"    "python3 /usr/libexec/kantanos/check-welcome"
check "kantan-app helper works"             "kantan-app status org.example.Nothing | grep -q uninstall"
check "file manager defaults present"       "grep -q ShowFullPath=false /etc/xdg/dolphinrc"
check "file permissions sane"               "test \$(stat -c %a /etc/xdg/kwinrc) = 644"
check "file manager toolbar layout present" "grep -q commandToolBar /etc/skel/.local/share/kxmlgui5/dolphin/dolphinui.rc"
check "file manager saved layout present"  "grep -q ^State= /etc/skel/.local/state/dolphinstaterc"
check "file manager sidebar setup runs"    "test -x /usr/libexec/kantanos/files-setup && grep -q files-setup /etc/xdg/plasma-workspace/env/kantanos-files.sh"
mkdir -p /tmp/fmtest/Documents
check "sidebar setup writes the sidebar"   "HOME=/tmp/fmtest XDG_DATA_HOME=/tmp/fmtest/d /usr/libexec/kantanos/files-setup; grep -q applications:/ /tmp/fmtest/d/user-places.xbel && xmllint --noout /tmp/fmtest/d/user-places.xbel"
check "file manager window rule present"   "grep -q wmclass=dolphin /etc/xdg/kwinrulesrc"
check "file manager is named Files"        "grep -q ^Name=Files /usr/share/applications/org.kde.dolphin.desktop"
check "mode chooser program is valid"      "test -x /usr/libexec/kantanos/modes && python3 -m py_compile /usr/libexec/kantanos/modes"
check "mode chooser has its four modes"    "test \$(ls /usr/share/kantanos/modes/*.mode | wc -l) -ge 4 && test -s /usr/share/kantanos/looks/light/icons/tv.svg"
check "mode chooser screen loads"          "HOME=/tmp/fmtest QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software timeout 10 /usr/libexec/kantanos/modes; test \$? = 124"
check "mode chooser starts at login"       "grep -q -- --login /etc/xdg/autostart/kantanos-modes.desktop"
check "mode chooser is on the dock"        "grep -q kantanos-modes.desktop /usr/share/plasma/look-and-feel/org.kantanos.desktop/contents/layouts/org.kde.plasma.desktop-layout.js && test -f /usr/share/applications/kantanos-modes.desktop"
check "mode chooser window rule present"   "grep -q wmclass=kantanos-modes /etc/xdg/kwinrulesrc"
check "starter apps wait and run at idle priority" "grep -q IOSchedulingClass=idle /usr/lib/systemd/system/kantanos-flatpak-setup.service && grep -q sleep.180 /usr/lib/systemd/system/kantanos-flatpak-setup.service"
check "login display server has a long start limit" "grep -q TimeoutStartSec=300 /usr/lib/systemd/user/plasma-login-kwin_wayland.service.d/10-kantanos.conf && test -f /usr/lib/systemd/user/plasma-login-kwin_wayland.service"
check "bluetooth boot argument is built in" "grep -q bluetooth.disable_ertm=1 /usr/lib/bootc/kargs.d/10-kantanos.toml"
check "daily update timer enabled"       "systemctl is-enabled uupd.timer"
check "update recipes parse"                "just --justfile /usr/share/ublue-os/justfile --list | grep -q kantan-undo-update"
. /usr/lib/os-release
if [ -n "$KANTAN_IMAGE" ]; then
check "image knows its update address"      "grep -q \"docker://$KANTAN_IMAGE\" /usr/share/ublue-os/image-info.json"
check "signing public key present"          "grep -q \"BEGIN PUBLIC KEY\" /etc/pki/containers/kantanos.pub"
check "only signed updates are accepted"    "jq -e --arg r \"$KANTAN_IMAGE\" \".transports.docker[\\\$r][0].type == \\\"sigstoreSigned\\\"\" /etc/containers/policy.json"
check "signatures are looked up"            "grep -q \"$KANTAN_IMAGE\" /etc/containers/registries.d/kantanos.yaml"
else
echo "NOTE  no update address in this build (tools/registry.conf is empty)"
fi
ls /usr/share/applications | grep -i fcitx
exit $fail
'
