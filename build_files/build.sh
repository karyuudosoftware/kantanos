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
chmod 0755 /usr/libexec/kantanos/* /usr/bin/kantan-*

### 2. Packages ---------------------------------------------------------------
# Japanese input (fcitx5 + Mozc), Japanese locale, the Inter UI font, a media player.
dnf5 -y install \
    fcitx5 fcitx5-mozc fcitx5-qt fcitx5-gtk fcitx5-configtool \
    glibc-langpack-ja langpacks-core-ja \
    rsms-inter-fonts rsms-inter-vf-fonts \
    mpv
# Qt for Python: the "What would you like to do?" screen and Force Quit are written with it.
# Installed explicitly because the base image stopped including it (Nov 2026).
dnf5 -y install python3-pyside6
python3 -c "import PySide6.QtQuick"

# Windows programs (kantan-windows): Wine with its .NET and web-view helpers.
dnf5 -y install wine wine-mono mingw32-wine-gecko mingw64-wine-gecko
# Windows virtual machine (/usr/libexec/kantanos/windows-vm): QEMU run by the user, a software
# TPM chip, the setup window, and xorriso for the answers disc. Secure Boot firmware
# (edk2-ovmf) and the Remote Desktop client (freerdp) are already in the base.
dnf5 -y install qemu-system-x86-core qemu-img qemu-ui-gtk swtpm swtpm-tools xorriso

# Fedora's Wine 11 keeps its Windows libraries in /usr/lib64/wine-wow64, which the SELinux
# policy does not label yet (it only knows /usr/lib*/wine). Without the textrel label every
# 32-bit Windows program, most installers included, is refused ("failed to set protection").
# (written as /usr/lib/...: the policy treats /usr/lib64 as the same place as /usr/lib)
WINE_FC='/usr/lib/wine-wow64(/.*)?'
if command -v semanage >/dev/null; then
    semanage fcontext -a -t textrel_shlib_t "$WINE_FC" 2>/dev/null || semanage fcontext -m -t textrel_shlib_t "$WINE_FC"
else
    echo "$WINE_FC    system_u:object_r:textrel_shlib_t:s0" >> /etc/selinux/targeted/contexts/files/file_contexts.local
fi
matchpathcon /usr/lib64/wine-wow64/wine/i386-windows/ntdll.dll | grep -q textrel_shlib_t
# Wine's own menu entries (Notepad, Wordpad, Regedit, uninstaller...) clutter search and
# beat installed programs like Notepad++; KantanOS Welcome → Windows covers what matters.
for f in /usr/share/applications/wine-*.desktop; do
    [ -f "$f" ] || continue
    grep -q '^NoDisplay=' "$f" && sed -i 's/^NoDisplay=.*/NoDisplay=true/' "$f" || sed -i '/^\[Desktop Entry\]/a NoDisplay=true' "$f"
done

# Local AI for the KantanOS Helper: Ollama with its Vulkan backend (runs on NVIDIA, AMD and
# Intel graphics). Off until the user turns it on in the Helper (kantanos-ollama user
# service); the model is downloaded then, into their home folder.
dnf5 -y install ollama ollama-vulkan
# The Helper's voice: Piper text-to-speech on this PC (the voice itself downloads on first use)
dnf5 -y install python3-piper-tts pipewire-utils
python3 -c "import piper"
# ...and its ears: whisper.cpp speech recognition (CPU build bundled in the Python module;
# the speech model downloads on first use, after asking)
dnf5 -y install python3-pywhispercpp
python3 -c "import pywhispercpp.model, numpy"
# ...and its eyes (Kan-chan, only if the person switches it on): OpenCV face detection and
# recognition. The slim pip build (about 170 MB); Fedora's python3-opencv pulls in 730 MB.
pip3 install --prefix=/usr --no-deps --only-binary=:all: --root-user-action=ignore --no-cache-dir \
    opencv-python-headless==5.1.0.95
python3 -c "import cv2; cv2.FaceDetectorYN; cv2.FaceRecognizerSF"
# The face models from the OpenCV model zoo: YuNet (MIT) and SFace (Apache 2.0)
VISION=/usr/share/kantanos/kanchan/vision
mkdir -p "$VISION" /usr/share/licenses/kantanos-kanchan-vision
ZOO=https://github.com/opencv/opencv_zoo/raw/main/models
curl -fsSL --retry 3 -o "$VISION/face_detection_yunet_2023mar.onnx" "$ZOO/face_detection_yunet/face_detection_yunet_2023mar.onnx"
curl -fsSL --retry 3 -o "$VISION/face_recognition_sface_2021dec.onnx" "$ZOO/face_recognition_sface/face_recognition_sface_2021dec.onnx"
curl -fsSL --retry 3 -o /usr/share/licenses/kantanos-kanchan-vision/YuNet-LICENSE "$ZOO/face_detection_yunet/LICENSE"
curl -fsSL --retry 3 -o /usr/share/licenses/kantanos-kanchan-vision/SFace-LICENSE "$ZOO/face_recognition_sface/LICENSE"
sha256sum -c - <<'SUMS'
8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4  /usr/share/kantanos/kanchan/vision/face_detection_yunet_2023mar.onnx
0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79  /usr/share/kantanos/kanchan/vision/face_recognition_sface_2021dec.onnx
SUMS
systemctl disable ollama.service 2>/dev/null || true

# Picture helper, "Make a picture" / "Fix a photo": stable-diffusion.cpp (MIT), its official
# Linux Vulkan build (NVIDIA, AMD and Intel graphics), pinned and checked. The picture model
# itself (FLUX.2 klein, Apache 2.0) downloads on first use, after asking.
SD_TAG=master-1106-532d2c1
SD_ZIP=sd-master-532d2c1-bin-Linux-Ubuntu-26.04-x86_64-vulkan.zip
curl -fsSL --retry 3 -o /tmp/sd.zip "https://github.com/leejet/stable-diffusion.cpp/releases/download/$SD_TAG/$SD_ZIP"
sha256sum -c - <<'SUMS'
ca30fe17f1735cdfb4c8561b75799070c25cc86a9e5438f4c0e1b163baae4e12  /tmp/sd.zip
SUMS
mkdir -p /usr/lib/kantanos/sd /usr/share/licenses/kantanos-sd
unzip -q -o /tmp/sd.zip -d /usr/lib/kantanos/sd
rm -f /tmp/sd.zip /usr/lib/kantanos/sd/start-server.* /usr/lib/kantanos/sd/sd-server
mv /usr/lib/kantanos/sd/*.txt /usr/share/licenses/kantanos-sd/
chmod 755 /usr/lib/kantanos/sd/sd-cli
LD_LIBRARY_PATH=/usr/lib/kantanos/sd /usr/lib/kantanos/sd/sd-cli --help > /tmp/sd-help.txt
grep -q -- --diffusion-model /tmp/sd-help.txt && rm /tmp/sd-help.txt

# Backups (/usr/libexec/kantanos/backup): restic makes locked, only-what-changed backups;
# rclone lets it use Google Drive and OneDrive.
dnf5 -y install restic rclone

# Easier to see and hear (/usr/libexec/kantanos/accessibility): Orca reads the screen (already in
# the base image; installed here so it can never go missing). Kan-chan's calendar reminders read
# the person's own calendar links with icalendar (repeats worked out with dateutil).
dnf5 -y install orca python3-icalendar python3-dateutil
python3 -c "import icalendar, dateutil.rrule"

# Letters and documents (/usr/bin/kantan-docs): reading scanned letters and photos of pages
# (tesseract; its English and Japanese data are already in the base), PDFs with poppler.
dnf5 -y install tesseract tesseract-langpack-eng tesseract-langpack-jpn poppler-utils
tesseract --list-langs | grep -qx jpn

# Watch TV: libmpv draws the picture inside the TV app; ffmpeg (already in Bazzite) records.
dnf5 -y install mpv-libs
# The recorder runs for everyone who signs in, idle until something is due.
systemctl --global enable kantanos-tv-recorder.service

# Game Mode library sync (/usr/libexec/kantanos/games-sync): games installed in Heroic or Lutris
# appear in Steam's Game Mode by themselves (watched for every account; idle otherwise).
systemctl --global enable kantanos-games-sync.path

# Virus scanning: ClamAV, its list of known viruses kept up to date in the background, and
# "Scan for viruses" in Files (/usr/libexec/kantanos/virus-scan).
dnf5 -y install clamav clamav-update
sed -i 's/^Example/#Example/' /etc/freshclam.conf 2>/dev/null || true
systemctl enable clamav-freshclam.service

# Firewall: the KantanOS zone (only the features that need incoming connections) instead of
# Fedora Workstation's, which allows every port above 1024 and SSH.
sed -i 's/^DefaultZone=.*/DefaultZone=KantanOS/' /etc/firewalld/firewalld.conf
grep -q '^DefaultZone=KantanOS' /etc/firewalld/firewalld.conf
firewall-offline-cmd --check-config >/dev/null

# Windows-drive notice (Bazzite's NTFS/exFAT monitor): KantanOS name and plainer English.
NTFS_NOTE=/usr/libexec/ntfs-exfat-monitor-script
if [ -f "$NTFS_NOTE" ]; then
    sed -i -e 's/^sender="Bazzite"/sender="KantanOS"/' \
        -e 's/header=("Unsupported filesystem")/header=("Windows drive connected")/' \
        -e 's/warning=("You have mounted an NTFS\/exFAT (Windows) partition\. You can use it for storing data, however running games from Windows drives will cause problems\.")/warning=("Your files on this Windows (NTFS or exFAT) drive work normally. Only games should go on a KantanOS drive: games installed on a Windows drive often fail to start.")/' \
        "$NTFS_NOTE"
    grep -q 'sender="KantanOS"' "$NTFS_NOTE" && grep -q "Windows drive connected" "$NTFS_NOTE"
fi

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
    # The terminal banner and the base's helper commands read these: name the KantanOS
    # image and the tag it is published under (latest), not the base's "stable".
    jq --arg ref "ostree-image-signed:docker://${KANTAN_IMAGE}"        --arg name "${KANTAN_IMAGE##*/}" --arg vendor "$(cut -d/ -f2 <<<"$KANTAN_IMAGE")"        '."image-ref" = $ref | ."image-name" = $name | ."image-vendor" = $vendor | ."image-tag" = "latest" | ."image-branch" = "latest"'        "$INFO" > /tmp/info.json
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
# One colour scheme per look (tools/looks.py): Breeze Light or Dark with the look's accent.
for conf in /usr/share/kantanos/looks/*/look.conf; do
    ( . "$conf"
      sed -e "s/^Name=.*/Name=Kantan ${LABEL}/" \
          -e '/^Name\[/d' \
          -e "s/61,174,233/${ACCENT}/g" \
          -e "s/29,153,243/${ACCENT_HOVER}/g" \
          "/usr/share/color-schemes/${BASE_SCHEME}.colors" > "/usr/share/color-schemes/${SCHEME}.colors" )
done
# New users start with the default look.
( . "/usr/share/kantanos/looks/$(cat /usr/share/kantanos/looks/default)/look.conf"
  sed -i -e "s|^ColorScheme=.*|ColorScheme=${SCHEME}|" -e "s|^Theme=breeze.*|Theme=${ICON_THEME}|" \
      /usr/share/plasma/look-and-feel/org.kantanos.desktop/contents/defaults )

# Make the KantanOS look the default for new users.
sed -i 's|^LookAndFeelPackage=.*|LookAndFeelPackage=org.kantanos.desktop|' /etc/xdg/kdeglobals
sed -i 's|^font=Noto Sans,10|font=Inter Variable,10|; s|^menuFont=Noto Sans,10|menuFont=Inter Variable,10|; s|^toolBarFont=Noto Sans,9|toolBarFont=Inter Variable,9|; s|^smallestReadableFont=Noto Sans,8|smallestReadableFont=Inter Variable,8|' /etc/xdg/kdeglobals

# Lock screen and login screen use the KantanOS wallpaper too.
LOCK_IMAGE="/usr/share/kantanos/looks/$(cat /usr/share/kantanos/looks/default)/lock.png"
cat > /etc/xdg/kscreenlockerrc <<EOF
[Greeter][Wallpaper][org.kde.image][General]
Image=${LOCK_IMAGE}
PreviewImage=${LOCK_IMAGE}
EOF

# Login screen (Plasma Login Manager) wallpaper.
sed -i "s|file:///usr/share/backgrounds/default.jxl|file://${LOCK_IMAGE}|g" /usr/lib/plasmalogin/defaults.conf

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
# ...and in its window titles ("Documents — Files", "ドキュメント — ファイル"): a one-line
# translation in a made-up language "kantanos" that /usr/libexec/kantanos/files-name puts first
# for Dolphin only (see there why), installed in Dolphin's place.
for l in kantanos:Files kantanos_ja:ファイル; do
    mkdir -p "/usr/share/locale/${l%%:*}/LC_MESSAGES"
    printf 'msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n\nmsgid "Dolphin"\nmsgstr "%s"\n' "${l#*:}" \
        | msgfmt -o "/usr/share/locale/${l%%:*}/LC_MESSAGES/dolphin.mo" -
done
mv /usr/bin/dolphin /usr/libexec/kantanos/dolphin-bin
install -m 0755 /usr/libexec/kantanos/files-name /usr/bin/dolphin

# Spotlight-style search: Win+Space opens it too (Cmd+Space on a Mac), besides Alt+Space.
sed -i 's|^X-KDE-Shortcuts=Alt+Space,Alt+F2,Search$|X-KDE-Shortcuts=Meta+Space,Alt+Space,Alt+F2,Search|'     /usr/share/kglobalaccel/org.kde.krunner.desktop
grep -q '^X-KDE-Shortcuts=Meta+Space' /usr/share/kglobalaccel/org.kde.krunner.desktop

# The Welcome app's search plugin calls its results "Bazzite Portal Actions". The name is
# compiled into the plugin, so swap it for a text of exactly the same length (22 letters).
YR=/usr/lib64/qt6/plugins/kf6/krunner/krunner-yafti.so
if [ -f "$YR" ]; then
    perl -pi -e 's/Bazzite Portal Actions/KantanOS Welcome Items/g' "$YR"
    ! grep -q "Bazzite Portal Actions" "$YR"
fi

# Double-clicking a Windows program (.exe, .msi) installs or runs it through kantan-windows.
python3 - <<'PY'
import configparser, os
path = "/etc/xdg/mimeapps.list"
c = configparser.ConfigParser(interpolation=None, strict=False)
c.optionxform = str
if os.path.exists(path):
    c.read(path, encoding="utf-8")
if not c.has_section("Default Applications"):
    c.add_section("Default Applications")
for m in ("application/x-ms-dos-executable", "application/x-msdownload", "application/x-msi",
          "application/x-ms-shortcut", "application/vnd.microsoft.portable-executable",
          "application/x-msdos-program"):
    c.set("Default Applications", m, "kantanos-windows-program.desktop")
# Double-clicking an Android app (.apk) starts Android if needed and installs it (kantan-android).
c.set("Default Applications", "application/vnd.android.package-archive", "kantanos-android-install.desktop")
with open(path, "w", encoding="utf-8") as fh:
    c.write(fh, space_around_delimiters=False)
PY
grep -q 'x-msi=kantanos-windows-program.desktop' /etc/xdg/mimeapps.list

# Installed systems get the Windows-style local hardware clock once (the installer writes UTC).
systemctl enable kantanos-local-clock.service

# If the installer finished without a normal user account (only the Root Account page filled
# in), KDE's first-start wizard asks for one before the login screen; on every other PC it
# marks itself done (/usr/libexec/kantanos/first-user-check, plasma-setup.service.d).
dnf5 -y install plasma-setup efibootmgr
systemctl enable plasma-setup.service
# A firmware start-up entry for KantanOS when the installer didn't make one (seen on a real PC)
systemctl enable kantanos-boot-entry.service

# The system drive is called "KantanOS" in Files, not the installer's label "root" (once).
systemctl enable kantanos-drive-label.service

# On a screen whose best picture is bigger than 1080p, the first picture is 1080p (the person can
# pick 4K in Display settings). Stops a black login screen on older PCs with 4K TVs.
systemctl enable kantanos-safe-picture.service

# Starter apps (browser, viewers, media player) are installed on first boot.
systemctl enable kantanos-flatpak-setup.service

# Block bad sites: the PC fetches Dan Pollock's list (someonewhocares.org/hosts) itself, soon
# after start-up and then about weekly, and writes the names into its own part of /etc/hosts;
# the safe look-up service (Quad9) is set in the same step. Both are on until someone turns
# them off in Welcome → Tools → Block bad sites (/usr/libexec/kantanos/site-blocker).
systemctl enable kantanos-site-blocker.timer

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
