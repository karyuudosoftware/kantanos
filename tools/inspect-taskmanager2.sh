#!/bin/bash
# The public task-list QML module a custom dock widget can use (org.kde.taskmanager).
podman run --rm --entrypoint bash localhost/kantanos:latest -c '
Q=/usr/lib64/qt6/qml/org/kde/taskmanager; ls $Q
T=$(ls $Q/*.qmltypes | head -1)
echo "== TasksModel properties and methods"
awk "/name: \"TaskManager::TasksModel\"/,/^    }$/" $T | grep -E "Property \{ name|Method \{ name|Signal \{ name|exports" | sed "s/ *Property { name: /P /; s/ *Method { name: /M /; s/ *Signal { name: /S /" | head -90
echo "== roles"; awk "/name: \"TaskManager::AbstractTasksModel\"/,/^    }$/" $T | grep -E "Enum|name:|values" | head -70
'
