/*
 * Kan-chan on the desktop: she blinks and sways a little; click her to open her window.
 * When she says her daily hello (kanchan --check-in), it shows in a speech bubble for a
 * minute (read from buddy.txt in her data folder, only if written in the last 10 minutes).
 * "Sit on my desktop" in her window adds or removes this widget.
 */
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PC
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    property string pack: "file:///usr/share/kantanos/helper/characters/kan-chan/"
    property bool ownPicture: false
    property string frame: "idle"
    property string bubble: ""
    property string lastSaid: ""

    preferredRepresentation: fullRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    toolTipMainText: "Kan-chan"
    toolTipSubText: i18n("Click me to talk")

    fullRepresentation: Item {
        Layout.minimumWidth: Kirigami.Units.gridUnit * 6
        Layout.minimumHeight: Kirigami.Units.gridUnit * 8
        Layout.preferredWidth: Kirigami.Units.gridUnit * 11
        Layout.preferredHeight: Kirigami.Units.gridUnit * 15

        Rectangle {
            id: speech
            visible: root.bubble !== ""
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            width: Math.min(parent.width, said.implicitWidth + Kirigami.Units.largeSpacing * 2)
            height: said.implicitHeight + Kirigami.Units.largeSpacing * 2
            radius: Kirigami.Units.gridUnit * 0.8
            color: Kirigami.Theme.backgroundColor
            border.color: Kirigami.Theme.highlightColor
            border.width: 2
            PC.Label {
                id: said
                anchors.centerIn: parent
                width: Math.min(implicitWidth, speech.parent.width - Kirigami.Units.largeSpacing * 2)
                text: root.bubble
                wrapMode: Text.Wrap
                horizontalAlignment: Text.AlignHCenter
            }
        }

        Image {
            id: face
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: sway.value
            width: parent.width
            height: parent.height - (speech.visible ? speech.height + Kirigami.Units.smallSpacing : 0)
            source: root.ownPicture ? root.pack + "idle.png" : root.pack + root.frame + ".svg"
            sourceSize.width: width * 2
            sourceSize.height: height * 2
            fillMode: Image.PreserveAspectFit
            smooth: true
            QtObject { id: sway; property real value: 0 }
            SequentialAnimation {
                running: true
                loops: Animation.Infinite
                NumberAnimation { target: sway; property: "value"; from: 0; to: 5; duration: 1600; easing.type: Easing.InOutSine }
                NumberAnimation { target: sway; property: "value"; from: 5; to: 0; duration: 1600; easing.type: Easing.InOutSine }
            }
        }

        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onEntered: root.frame = "happy"
            onExited: root.frame = "idle"
            onClicked: {
                root.bubble = ""
                run.exec("kstart --application kantanos-kanchan")
            }
        }
    }

    Timer {   // blink now and then
        interval: 4200
        running: true
        repeat: true
        onTriggered: {
            if (root.frame === "idle") {
                root.frame = "blink"
                unblink.start()
            }
            interval = 3000 + Math.random() * 4000
        }
    }
    Timer { id: unblink; interval: 160; onTriggered: if (root.frame === "blink") root.frame = "idle" }
    Timer { id: quiet; interval: 60000; onTriggered: { root.bubble = ""; root.frame = "idle" } }

    readonly property string sayCmd: "f=\"${XDG_DATA_HOME:-$HOME/.local/share}/kantanos/kanchan/buddy.txt\"; "
        + "[ -n \"$(find \"$f\" -mmin -10 2>/dev/null)\" ] && cat \"$f\"; true # buddy-say"
    Timer {   // her daily hello, as a speech bubble
        interval: 30000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            run.exec(root.sayCmd)
            run.exec(root.packCmd)
        }
    }

    // which character: a made one in the home folder (Kan-chan → Make a character) or Kan-chan
    readonly property string packCmd: "c=$(sed -n 's/.*\"character\": *\"\\([^\"]*\\)\".*/\\1/p' "
        + "\"${XDG_CONFIG_HOME:-$HOME/.config}/kantanos/helper.json\" 2>/dev/null); "
        + "d=\"${XDG_DATA_HOME:-$HOME/.local/share}/kantanos/helper/characters/$c\"; "
        + "[ -n \"$c\" ] && [ \"$c\" != kan-chan ] && [ -d \"$d\" ] && echo \"$d\" && ls \"$d\"; true # buddy-pack"

    P5Support.DataSource {
        id: run
        engine: "executable"
        function exec(cmd) { connectSource(cmd) }
        onNewData: (source, data) => {
            disconnectSource(source)
            if (source === root.packCmd) {
                var lines = (data.stdout || "").split("\n").filter(l => l.trim() !== "")
                if (lines.length > 0) {
                    root.pack = "file://" + lines[0] + "/"
                    root.ownPicture = lines.indexOf("idle.png") >= 0 && lines.indexOf("idle.svg") < 0
                } else {
                    root.pack = "file:///usr/share/kantanos/helper/characters/kan-chan/"
                    root.ownPicture = false
                }
                return
            }
            if (source !== root.sayCmd) return
            var text = (data.stdout || "").trim()
            if (text !== "" && text !== root.lastSaid) {
                root.lastSaid = text
                root.bubble = text
                root.frame = "happy"
                quiet.restart()
            }
        }
    }
}
