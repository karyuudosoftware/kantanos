# Runs as the test user in the VM: executes /tmp/shell-script.js in the running Plasma shell.
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
busctl --user call org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell evaluateScript s "$(cat /tmp/shell-script.js)"
