#!/usr/bin/bash
# KantanOS image build. Runs inside the Bazzite base image at container build time.
set -euxo pipefail

KANTAN_VERSION="${KANTAN_VERSION:-0.1.0}"
KANTAN_EDITION="${KANTAN_EDITION:-full}"
KANTAN_BUILD="${KANTAN_BUILD:-dev}"
KANTAN_IMAGE="${KANTAN_IMAGE:-}"

### 1. System files -----------------------------------------------------------
# The sources live on a Windows drive, so do not trust their permissions.
cp -rT --no-preserve=mode,ownership /ctx/system /
chmod 0755 /usr/libexec/kantanos/* /usr/bin/kantan-app

### 2. Packages ---------------------------------------------------------------
# Japanese input (fcitx5 + Mozc), Japanese locale, the Inter UI font, a media player.
dnf5 -y install \
    fcitx5 fcitx5-mozc fcitx5-qt fcitx5-gtk fcitx5-configtool \
    glibc-langpack-ja langpacks-core-ja \
    rsms-inter-fonts rsms-inter-vf-fonts \
    mpv

### 3. Identity ---------------------------------------------------------------
# ID stays "bazzite" so the Universal Blue tooling keeps working; the names change.
BASE_VERSION="$(. /usr/lib/os-release && echo "$OSTREE_VERSION")"
sed -i \
    -e "s|^NAME=.*|NAME=\"KantanOS\"|" \
    -e "s|^PRETTY_NAME=.*|PRETTY_NAME=\"KantanOS ${KANTAN_VERSION}\"|" \
    -e "s|^VERSION=.*|VERSION=\"${KANTAN_VERSION} (Bazzite ${BASE_VERSION})\"|" \
    -e "s|^LOGO=.*|LOGO=kantanos|" \
    -e "s|^DEFAULT_HOSTNAME=.*|DEFAULT_HOSTNAME=\"kantanos\"|" \
    -e "s|^BOOTLOADER_NAME=.*|BOOTLOADER_NAME=\"KantanOS ${KANTAN_VERSION}\"|" \
    -e "s|^ANSI_COLOR=.*|ANSI_COLOR=\"0;38;2;108;123;255\"|" \
    /usr/lib/os-release
cat >> /usr/lib/os-release <<EOF
KANTAN_VERSION="${KANTAN_VERSION}"
KANTAN_EDITION="${KANTAN_EDITION}"
KANTAN_BUILD="${KANTAN_BUILD}"
KANTAN_IMAGE="${KANTAN_IMAGE}"
EOF

### 3b. Updates ---------------------------------------------------------------
# The base already checks for updates every day (uupd.timer) and installs them for the
# next restart. Here the image learns its own address and to trust only KantanOS-signed
# images from it.
if [ -n "$KANTAN_IMAGE" ]; then
    INFO=/usr/share/ublue-os/image-info.json
    jq --arg ref "ostree-image-signed:docker://${KANTAN_IMAGE}" '."image-ref" = $ref' "$INFO" > /tmp/info.json
    install -m 0644 /tmp/info.json "$INFO"
    if [ -f /etc/pki/containers/kantanos.pub ]; then
        jq --arg repo "$KANTAN_IMAGE" '.transports.docker[$repo] = [{
              "type": "sigstoreSigned",
              "keyPath": "/etc/pki/containers/kantanos.pub",
              "signedIdentity": {"type": "matchRepository"}
            }]' /etc/containers/policy.json > /tmp/policy.json
        install -m 0644 /tmp/policy.json /etc/containers/policy.json
        printf 'docker:\n  %s:\n    use-sigstore-attachments: true\n' "$KANTAN_IMAGE" \
            > /etc/containers/registries.d/kantanos.yaml
    fi
fi
systemctl enable uupd.timer

### 4. Desktop defaults -------------------------------------------------------
# Colour scheme: Breeze Dark with the KantanOS indigo accent.
sed -e 's/^Name=.*/Name=Kantan Glass/' \
    -e '/^Name\[/d' \
    -e 's/61,174,233/108,123,255/g' \
    -e 's/29,153,243/122,162,255/g' \
    /usr/share/color-schemes/BreezeDark.colors > /usr/share/color-schemes/KantanGlass.colors

# Make the KantanOS look the default for new users.
sed -i 's|^LookAndFeelPackage=.*|LookAndFeelPackage=org.kantanos.desktop|' /etc/xdg/kdeglobals
sed -i 's|^font=Noto Sans,10|font=Inter Variable,10|; s|^menuFont=Noto Sans,10|menuFont=Inter Variable,10|; s|^toolBarFont=Noto Sans,9|toolBarFont=Inter Variable,9|; s|^smallestReadableFont=Noto Sans,8|smallestReadableFont=Inter Variable,8|' /etc/xdg/kdeglobals

# Lock screen and login screen use the KantanOS wallpaper too.
cat > /etc/xdg/kscreenlockerrc <<'EOF'
[Greeter][Wallpaper][org.kde.image][General]
Image=/usr/share/wallpapers/KantanOS/contents/images/3840x2160.png
PreviewImage=/usr/share/wallpapers/KantanOS/contents/images/3840x2160.png
EOF

# Login screen (Plasma Login Manager) wallpaper.
sed -i 's|file:///usr/share/backgrounds/default.jxl|file:///usr/share/wallpapers/KantanOS/contents/images/3840x2160.png|g' /usr/lib/plasmalogin/defaults.conf

# No Bazzite announcements, and Steam does not start by itself at login.
rm -f /etc/skel/.config/autostart/steam.desktop /etc/xdg/autostart/bazzite-announcement.desktop

# The welcome app is the Bazzite Portal engine with KantanOS content (system_files replaces
# its yafti.yml and its autostart entry); rename what the engine itself writes and shows.
for f in /usr/bin/yafti_gtk.py /usr/share/applications/io.github.ublue_os.yafti_gtk.desktop; do
    sed -i -e 's|Bazzite Portal|KantanOS Welcome|g' -e 's|Comment=Helps you setup Bazzite|Comment=Helps you set up KantanOS|' -e 's|Icon=io.github.ublue_os.yafti_gtk|Icon=kantanos|' "$f"
done
sed -i -e '/^Name\[/d' -e '/^Comment\[/d' -e 's|^Keywords=.*|Keywords=kantanos;welcome;setup;apps;|' /usr/share/applications/io.github.ublue_os.yafti_gtk.desktop

# The file manager is simply called "Files" in menus and on the dock (English name only;
# other languages keep their own translation). Its Explorer-style layout comes from
# system_files: dolphinrc, the toolbar definition and saved layout in /etc/skel, a window
# rule for its opening size, and files-setup for the sidebar.
sed -i -e 's|^Name=Dolphin$|Name=Files|' -e 's|^GenericName=File Manager$|GenericName=File Manager (Dolphin)|' \
    /usr/share/applications/org.kde.dolphin.desktop

# Starter apps (browser, viewers, media player) are installed on first boot.
systemctl enable kantanos-flatpak-setup.service

gtk-update-icon-cache -f /usr/share/icons/hicolor || true

### 5. Boot splash ------------------------------------------------------------
# Reuse the stock spinner artwork, with the KantanOS logo as the watermark.
THEME=/usr/share/plymouth/themes/kantanos
cp -n /usr/share/plymouth/themes/spinner/*.png "$THEME/"
sed -i 's|^Theme=.*|Theme=kantanos|' /usr/share/plymouth/plymouthd.defaults

KVER="$(ls /usr/lib/modules | head -n1)"
export DRACUT_NO_XATTR=1
/usr/bin/dracut --no-hostonly --kver "$KVER" --reproducible --zstd --add ostree \
    --tmpdir /tmp -f "/usr/lib/modules/$KVER/initramfs.img"
chmod 0600 "/usr/lib/modules/$KVER/initramfs.img"

### 5b. Repositories for the installer builder -----------------------------------
# Fedora keeps its repo definitions in /usr/share/dnf5/repos.d; the ISO builder
# (bootc-image-builder) only reads /etc/yum.repos.d, so mirror them there.
if [ -d /usr/share/dnf5/repos.d ]; then
    for f in /usr/share/dnf5/repos.d/*.repo; do
        [ -e "/etc/yum.repos.d/$(basename "$f")" ] || cp "$f" /etc/yum.repos.d/
    done
fi
dnf5 repolist

### 6. Clean up ---------------------------------------------------------------
dnf5 clean all
rm -rf /var/lib/dnf /tmp/* || true
