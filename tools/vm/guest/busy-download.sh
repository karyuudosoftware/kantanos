# Runs as root in the VM: starts a long Flatpak download in the background, standing in for
# the first-start starter apps, so an install from the Welcome app has to queue behind it.
flatpak uninstall --system -y --noninteractive com.github.dail8859.NotepadNext >/dev/null 2>&1
nohup flatpak install --system --noninteractive -y flathub org.gnome.TextEditor > /tmp/busy.log 2>&1 &
sleep 3; pgrep -af '(^|/)flatpak install' | head -1
