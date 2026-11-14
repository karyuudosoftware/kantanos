// KantanOS mode chooser: full-screen tiles for Desktop, Game Mode and so on, plus the
// look (colour style) picker. Data and actions come from the "backend" object
// (see /usr/libexec/kantanos/modes); colours come from backend.look.
import QtQuick
import QtQuick.Controls
import QtQuick.Window
import org.kde.layershell as LayerShell

Window {
    id: root
    visible: true
    flags: Qt.FramelessWindowHint
    width: Screen.width
    height: Screen.height
    color: look.OVERLAY
    title: "KantanOS"

    // An overlay surface: covers the whole screen including the top bar and dock, and
    // takes the keyboard, no matter which other window opened first.
    LayerShell.Window.scope: "kantanos-modes"
    LayerShell.Window.layer: LayerShell.Window.LayerOverlay
    LayerShell.Window.anchors: LayerShell.Window.AnchorTop | LayerShell.Window.AnchorBottom | LayerShell.Window.AnchorLeft | LayerShell.Window.AnchorRight
    LayerShell.Window.exclusionZone: -1
    LayerShell.Window.keyboardInteractivity: LayerShell.Window.KeyboardInteractivityExclusive

    readonly property var look: backend.look
    readonly property bool dark: look.DARK === "1"
    readonly property color ink: look.TEXT                        // text colour
    readonly property real u: Math.max(0.6, height / 1080)       // 1 unit = 1 px on a 1080p screen
    readonly property int tileCount: backend.modes.length + 1     // + "Add shortcut"
    // Up to six tiles sit in one row; more than that split evenly over two rows.
    readonly property int columns: tileCount <= 6 ? tileCount : Math.ceil(tileCount / 2)
    readonly property real gap: 28 * u
    readonly property real tileWidth: Math.min(250 * u, (width - 120 * u - (columns - 1) * gap) / columns)
    property int current: 0
    property string message: ""
    property bool adding: false
    readonly property bool blocked: backend.busy !== "" || message !== "" || adding

    function clampCurrent() { if (current >= tileCount) current = tileCount - 1; if (current < 0) current = 0 }
    function open(index) {
        if (blocked) return
        if (index === backend.modes.length) { adding = true; nameField.text = ""; addressField.text = ""; nameField.forceActiveFocus() }
        else backend.activate(index)
    }
    function iconFor(mode) { return mode.iconFile !== "" ? mode.iconFile : look.icons + "/" + mode.icon + ".svg" }

    Connections {
        target: backend
        function onFailed(text) { root.message = text }
        function onModesChanged() { root.clampCurrent() }
    }

    Image {
        anchors.fill: parent
        source: look.wallpaper
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
    }
    Rectangle { anchors.fill: parent; color: look.OVERLAY; opacity: Number(look.OVERLAY_OPACITY) }

    // Keyboard and remote: arrows move, Enter opens, Esc goes to the desktop.
    Item {
        id: keys
        anchors.fill: parent
        focus: !root.adding
        Keys.onPressed: (event) => {
            if (root.blocked) return
            if (event.key === Qt.Key_Right) { root.current = (root.current + 1) % root.tileCount; event.accepted = true }
            else if (event.key === Qt.Key_Left) { root.current = (root.current + root.tileCount - 1) % root.tileCount; event.accepted = true }
            else if (event.key === Qt.Key_Down) { if (root.current + root.columns < root.tileCount) root.current += root.columns; event.accepted = true }
            else if (event.key === Qt.Key_Up) { if (root.current - root.columns >= 0) root.current -= root.columns; event.accepted = true }
            else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter || event.key === Qt.Key_Space) { root.open(root.current); event.accepted = true }
            else if (event.key === Qt.Key_Escape) { backend.desktop(); event.accepted = true }
        }
    }

    // Clock
    Text {
        id: clock
        anchors { top: parent.top; right: parent.right; margins: 40 * root.u }
        color: root.ink; opacity: 0.85
        font.pixelSize: 30 * root.u
        Timer { interval: 1000; running: true; repeat: true; triggeredOnStart: true
                onTriggered: clock.text = Qt.formatDateTime(new Date(), Qt.locale().timeFormat(Locale.ShortFormat)) }
    }

    Column {
        anchors.centerIn: parent
        spacing: 46 * root.u

        Image {
            anchors.horizontalCenter: parent.horizontalCenter
            source: look.logo
            height: 190 * root.u
            fillMode: Image.PreserveAspectFit
            smooth: true; mipmap: true
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: backend.text.title
            color: root.ink
            font.pixelSize: 40 * root.u
            font.weight: Font.Light
        }

        Grid {
            id: grid
            anchors.horizontalCenter: parent.horizontalCenter
            columns: root.columns
            spacing: root.gap

            Repeater {
                model: root.tileCount
                delegate: Item {
                    id: tile
                    required property int index
                    readonly property bool isAdd: index === backend.modes.length
                    readonly property var mode: isAdd ? null : backend.modes[index]
                    readonly property bool selected: root.current === index
                    width: root.tileWidth
                    height: 270 * root.u

                    Rectangle {
                        id: glass
                        anchors.fill: parent
                        radius: 30 * root.u
                        color: tile.selected ? look.TILE_SELECTED : look.TILE
                        border.width: (tile.selected ? 3 : 1) * root.u
                        border.color: tile.selected ? look.ACCENT_HEX : look.TILE_BORDER
                        scale: tile.selected ? 1.06 : 1.0
                        Behavior on scale { NumberAnimation { duration: 120 } }
                        Behavior on color { ColorAnimation { duration: 120 } }

                        Column {
                            anchors.centerIn: parent
                            width: parent.width - 36 * root.u
                            spacing: 14 * root.u
                            Image {
                                anchors.horizontalCenter: parent.horizontalCenter
                                source: tile.isAdd ? look.icons + "/add.svg" : root.iconFor(tile.mode)
                                width: 96 * root.u; height: 96 * root.u
                                sourceSize.width: 192; sourceSize.height: 192
                                opacity: tile.isAdd ? 0.7 : 1.0
                            }
                            Text {
                                width: parent.width
                                horizontalAlignment: Text.AlignHCenter
                                text: tile.isAdd ? backend.text.add : tile.mode.name
                                color: root.ink
                                font.pixelSize: 25 * root.u
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Text {
                                width: parent.width
                                horizontalAlignment: Text.AlignHCenter
                                text: tile.isAdd ? backend.text.addHint
                                      : (tile.mode.installed ? tile.mode.comment : backend.text.install)
                                color: root.ink; opacity: 0.7
                                font.pixelSize: 15 * root.u
                                wrapMode: Text.WordWrap
                                maximumLineCount: 3
                                elide: Text.ElideRight
                            }
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        enabled: !root.blocked
                        onEntered: root.current = tile.index
                        onClicked: root.open(tile.index)
                    }

                    // Remove button on the user's own shortcuts
                    Rectangle {
                        visible: !tile.isAdd && tile.mode.custom && tile.selected && !root.blocked
                        anchors { top: parent.top; right: parent.right; margins: 4 * root.u }
                        width: 36 * root.u; height: width; radius: width / 2
                        color: removeArea.containsMouse ? "#e0c0392b" : "#80000000"
                        Text { anchors.centerIn: parent; text: "×"; color: "white"; font.pixelSize: 24 * root.u }
                        MouseArea { id: removeArea; anchors.fill: parent; hoverEnabled: true
                                    onClicked: backend.removeShortcut(tile.index) }
                    }
                }
            }
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: backend.text.hint
            color: root.ink; opacity: 0.5
            font.pixelSize: 16 * root.u
        }
    }

    // Bottom left: "show at startup" switch
    Row {
        anchors { left: parent.left; bottom: parent.bottom; margins: 36 * root.u }
        spacing: 12 * root.u
        Rectangle {
            width: 26 * root.u; height: width; radius: 6 * root.u
            anchors.verticalCenter: parent.verticalCenter
            color: backend.showAtLogin ? look.ACCENT_HEX : "transparent"
            border.color: root.ink; border.width: 1.5 * root.u
            Text { anchors.centerIn: parent; visible: backend.showAtLogin; text: "✓"; color: "white"; font.pixelSize: 18 * root.u }
        }
        Text { anchors.verticalCenter: parent.verticalCenter; text: backend.text.atStartup
               color: root.ink; opacity: 0.8; font.pixelSize: 18 * root.u }
    }
    MouseArea {
        anchors { left: parent.left; bottom: parent.bottom; margins: 24 * root.u }
        width: 420 * root.u; height: 52 * root.u
        enabled: !root.blocked
        onClicked: backend.setShowAtLogin(!backend.showAtLogin)
    }

    // Bottom centre: look picker, one swatch per colour style
    Row {
        anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 34 * root.u }
        spacing: 14 * root.u
        Text { anchors.verticalCenter: parent.verticalCenter; text: backend.text.look
               color: root.ink; opacity: 0.8; font.pixelSize: 18 * root.u; rightPadding: 6 * root.u }
        Repeater {
            model: backend.looks
            delegate: Item {
                id: swatch
                required property var modelData
                readonly property bool active: modelData.ID === look.ID
                width: 44 * root.u; height: width
                anchors.verticalCenter: parent.verticalCenter
                Rectangle {       // ring
                    anchors.fill: parent; radius: width / 2
                    color: "transparent"
                    border.width: (swatch.active ? 3 : 0) * root.u
                    border.color: look.ACCENT_HEX
                }
                Rectangle {       // the look's background colour with its gradient as the centre
                    anchors.centerIn: parent
                    width: 32 * root.u; height: width; radius: width / 2
                    color: swatch.modelData.SWATCH_BG
                    border.width: 1; border.color: root.dark ? "#60ffffff" : "#40000000"
                    Rectangle {
                        anchors.centerIn: parent
                        width: 18 * root.u; height: width; radius: width / 2
                        gradient: Gradient {
                            orientation: Gradient.Horizontal
                            GradientStop { position: 0; color: swatch.modelData.SWATCH_A }
                            GradientStop { position: 1; color: swatch.modelData.SWATCH_B }
                        }
                    }
                }
                MouseArea { id: swatchArea; anchors.fill: parent; hoverEnabled: true; enabled: !root.blocked
                            onClicked: backend.setLook(swatch.modelData.ID) }
                Text {            // name on hover or when active
                    visible: swatchArea.containsMouse
                    anchors { bottom: parent.top; horizontalCenter: parent.horizontalCenter; bottomMargin: 6 * root.u }
                    text: swatch.modelData.label
                    color: root.ink; font.pixelSize: 15 * root.u
                }
            }
        }
    }

    // Bottom right: power
    Row {
        anchors { right: parent.right; bottom: parent.bottom; margins: 36 * root.u }
        spacing: 14 * root.u
        Repeater {
            model: [ { key: "restart", label: backend.text.restart }, { key: "shutdown", label: backend.text.shutdown } ]
            delegate: Rectangle {
                required property var modelData
                width: label.implicitWidth + 36 * root.u; height: 44 * root.u; radius: height / 2
                color: powerArea.containsMouse ? look.TILE_SELECTED : look.TILE
                border.color: look.TILE_BORDER; border.width: 1
                Text { id: label; anchors.centerIn: parent; text: modelData.label; color: root.ink; font.pixelSize: 17 * root.u }
                MouseArea { id: powerArea; anchors.fill: parent; hoverEnabled: true; enabled: !root.blocked
                            onClicked: backend.power(modelData.key) }
            }
        }
    }

    // Overlay: installing, a message, or the "new shortcut" form
    Rectangle {
        anchors.fill: parent
        visible: root.blocked
        color: look.SHADE
        MouseArea { anchors.fill: parent; hoverEnabled: true }   // swallow clicks

        Rectangle {
            anchors.centerIn: parent
            width: 640 * root.u
            height: content.implicitHeight + 72 * root.u
            radius: 28 * root.u
            color: look.DIALOG
            border.color: look.TILE_BORDER; border.width: 1

            Column {
                id: content
                anchors.centerIn: parent
                width: parent.width - 72 * root.u
                spacing: 22 * root.u

                // Installing
                BusyIndicator { visible: backend.busy !== ""; running: visible; anchors.horizontalCenter: parent.horizontalCenter
                                width: 64 * root.u; height: 64 * root.u }
                Text { visible: backend.busy !== ""; width: parent.width; text: backend.busy; color: root.ink
                       font.pixelSize: 22 * root.u; wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignHCenter }

                // Message
                Text { visible: root.message !== ""; width: parent.width; text: root.message; color: root.ink
                       font.pixelSize: 22 * root.u; wrapMode: Text.WordWrap; horizontalAlignment: Text.AlignHCenter }
                Button { visible: root.message !== ""; anchors.horizontalCenter: parent.horizontalCenter
                         text: backend.text.ok; font.pixelSize: 18 * root.u
                         onClicked: { root.message = ""; keys.forceActiveFocus() } }

                // New shortcut
                Text { visible: root.adding; text: backend.text.addTitle; color: root.ink; font.pixelSize: 28 * root.u; font.weight: Font.DemiBold }
                Text { visible: root.adding; text: backend.text.name; color: root.ink; opacity: 0.8; font.pixelSize: 17 * root.u }
                TextField { id: nameField; visible: root.adding; width: parent.width; font.pixelSize: 20 * root.u
                            Keys.onReturnPressed: addressField.forceActiveFocus()
                            Keys.onEscapePressed: cancelButton.clicked() }
                Text { visible: root.adding; text: backend.text.address; color: root.ink; opacity: 0.8; font.pixelSize: 17 * root.u }
                TextField { id: addressField; visible: root.adding; width: parent.width; font.pixelSize: 20 * root.u
                            inputMethodHints: Qt.ImhUrlCharactersOnly
                            Keys.onReturnPressed: saveButton.clicked()
                            Keys.onEscapePressed: cancelButton.clicked() }
                Row {
                    visible: root.adding
                    anchors.right: parent.right
                    spacing: 14 * root.u
                    Button { id: cancelButton; text: backend.text.cancel; font.pixelSize: 18 * root.u
                             onClicked: { root.adding = false; keys.forceActiveFocus() } }
                    Button { id: saveButton; text: backend.text.save; font.pixelSize: 18 * root.u
                             enabled: nameField.text.trim() !== "" && addressField.text.trim() !== ""
                             onClicked: {
                                 if (backend.addShortcut(nameField.text, addressField.text)) { root.adding = false; keys.forceActiveFocus() }
                                 else addressField.forceActiveFocus()
                             } }
                }
            }
        }
    }
}
