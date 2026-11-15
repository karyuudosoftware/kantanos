#!/bin/bash
# How the dock's task manager (icontasks) is packaged: plain QML files or compiled into a plugin.
podman run --rm --entrypoint bash localhost/kantanos:latest -c '
for id in org.kde.plasma.taskmanager org.kde.plasma.icontasks; do
  echo "== $id"; ls -R /usr/share/plasma/plasmoids/$id 2>/dev/null | head -40
done
echo "== plugins"; ls /usr/lib64/qt6/plugins/plasma/applets/ | grep -i task
echo "== qml inside the plugin?"; strings /usr/lib64/qt6/plugins/plasma/applets/org.kde.plasma.taskmanager.so | grep -E "Task\.qml|main\.qml|TaskList" | head
echo "== plasma version"; rpm -q plasma-workspace plasma-desktop
'
