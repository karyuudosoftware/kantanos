#!/bin/bash
# Prints the facts about the base image that build.sh depends on.
IMG=${1:-ghcr.io/ublue-os/bazzite-nvidia-open:stable}
podman run --rm --entrypoint bash "$IMG" -c '
echo "=== os-release"; cat /usr/lib/os-release
echo "=== image-info"; cat /usr/share/ublue-os/image-info.json 2>/dev/null
echo "=== kernel"; ls /usr/lib/modules
echo "=== plasma"; rpm -q plasma-workspace kwin sddm plymouth dracut 2>&1
echo "=== look-and-feel"; ls /usr/share/plasma/look-and-feel
echo "=== kdeglobals files"; for f in /etc/xdg/kdeglobals /usr/share/kde-settings/kde-profile/default/xdg/kdeglobals /etc/xdg/kwinrc /etc/xdg/plasmarc /etc/xdg/kcminputrc; do echo "--- $f"; cat $f 2>/dev/null; done
echo "=== XDG dirs set"; grep -r XDG_CONFIG_DIRS /etc/profile.d /usr/lib/environment.d /etc/environment.d 2>/dev/null
echo "=== plasma layout overrides"; ls /usr/share/plasma/layout-templates /usr/share/plasma/shells/org.kde.plasma.desktop/contents 2>/dev/null; ls /etc/xdg/plasma-workspace 2>/dev/null; find /usr/share/plasma /etc/xdg -name "*layout*.js" 2>/dev/null | head -20
echo "=== plymouth"; ls /usr/share/plymouth/themes; plymouth-set-default-theme; cat /etc/plymouth/plymouthd.conf /usr/share/plymouth/plymouthd.defaults 2>/dev/null
echo "=== initramfs tooling"; ls /usr/libexec/containerbuild 2>/dev/null; ls /usr/bin | grep -i -E "initramfs|dracut"; ls /usr/lib/dracut/dracut.conf.d /etc/dracut.conf.d 2>/dev/null
echo "=== sddm"; ls /etc/sddm.conf.d /usr/lib/sddm/sddm.conf.d 2>/dev/null; cat /etc/sddm.conf.d/* /usr/lib/sddm/sddm.conf.d/* 2>/dev/null | head -60; ls /usr/share/sddm/themes
echo "=== ime / fonts / media"; rpm -q fcitx5 fcitx5-mozc fcitx5-qt fcitx5-gtk kcm-fcitx5 ibus ibus-mozc mpv vlc ffmpeg ffmpeg-free libavcodec-freeworld mesa-va-drivers nvidia-vaapi-driver libva-nvidia-driver rsms-inter-fonts rsms-inter-vf-fonts google-noto-sans-cjk-vf-fonts google-noto-sans-cjk-fonts langpacks-ja glibc-langpack-ja kde-l10n 2>&1
echo "=== just"; ls /usr/share/ublue-os/just; grep -n -E "import|custom" /usr/share/ublue-os/justfile 2>/dev/null
echo "=== color schemes"; ls /usr/share/color-schemes | head -30
echo "=== flatpak preinstall"; ls /usr/share/ublue-os/ /etc/flatpak/preinstall.d /usr/share/flatpak/preinstall.d 2>/dev/null
echo "=== repos"; ls /etc/yum.repos.d
echo "=== bazzite branding hooks"; ls /usr/share/ublue-os/bazzite 2>/dev/null | head; ls /usr/libexec | grep -i -E "bazzite|ublue" | head -40
echo "=== skel"; find /etc/skel -maxdepth 3 | head -40
'
