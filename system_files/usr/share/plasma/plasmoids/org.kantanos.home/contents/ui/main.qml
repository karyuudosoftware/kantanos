/*
 * KantanOS Smart home: the house temperature in the top bar, from the thermostat that
 * Home Assistant knows (for example a Google Nest). Click to change the temperature or to
 * switch the heating on or off.
 *
 * All the talking to Home Assistant is done by `kantan-home` (it keeps the sign-in key and
 * renews it); this widget only runs `kantan-home status` every minute and `kantan-home set`
 * when someone presses a button. "Smart home" in the app menu sets it up.
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

    property var info: ({ state: "loading" })
    property real pending: NaN            // target chosen with − / +, sent after a short pause
    readonly property bool ok: info.state === "ok"
    readonly property bool off: ok && info.mode === "off"
    readonly property bool heating: ok && info.action === "heating"
    readonly property bool cooling: ok && info.action === "cooling"
    readonly property bool single: ok && !off && info.target !== null && info.target !== undefined
    readonly property real target: !isNaN(pending) ? pending : (single ? info.target : NaN)

    function deg(t) {
        if (t === null || t === undefined || isNaN(t)) return "–"
        var step = ok ? info.step : 0.5
        return (step < 1 ? (Math.round(t * 2) / 2).toFixed(1).replace(/\.0$/, "") : Math.round(t)) + "°"
    }
    function modeName(m) {
        return ({ heat: i18n("Heat"), cool: i18n("Cool"), heat_cool: i18n("Auto"), auto: i18n("Auto"),
                  off: i18n("Off"), dry: i18n("Dry"), fan_only: i18n("Fan") })[m] || m
    }
    readonly property string message: ({
        loading: i18n("Checking the thermostat…"),
        setup: i18n("Smart home isn't set up yet"),
        no_thermostat: i18n("No thermostat chosen yet"),
        offline: i18n("Can't reach Home Assistant"),
        signed_out: i18n("Home Assistant signed this PC out"),
        error: i18n("Home Assistant had a problem")
    })[info.state] || ""
    readonly property string summary: {
        if (!ok) return message
        if (off) return i18n("Heating is off")
        if (info.mode === "unavailable") return i18n("The thermostat isn't answering")
        if (info.preset && info.preset.toLowerCase() === "eco") return i18n("Eco mode")
        if (single) {
            if (heating) return i18n("Heating to %1", deg(target))
            if (cooling) return i18n("Cooling to %1", deg(target))
            return i18n("Set to %1", deg(target))
        }
        if (info.low !== null && info.high !== null) return i18n("Keeping between %1 and %2", deg(info.low), deg(info.high))
        return modeName(info.mode)
    }

    toolTipMainText: ok ? info.name : i18n("Smart home")
    toolTipSubText: ok ? i18n("Inside: %1", deg(info.current)) + " · " + summary : message
    Plasmoid.icon: off ? "temperature-normal" : heating ? "temperature-warm" : cooling ? "temperature-cold" : "temperature-normal"

    P5Support.DataSource {
        id: sh
        engine: "executable"
        onNewData: (source, data) => {
            disconnectSource(source)
            if (source === "kantan-home status") {
                try { root.info = JSON.parse(data.stdout) } catch (e) { root.info = { state: "error" } }
            } else {
                if (data["exit code"] !== 0) root.pending = NaN
                later.restart()           // read back what the thermostat now says
            }
        }
    }
    function refresh() { sh.connectSource("kantan-home status") }
    function run(cmd) { sh.connectSource(cmd + " #" + Date.now()) }   // the comment makes each command new

    function nudge(by) {
        var t = isNaN(target) ? info.target : target
        pending = Math.min(info.max, Math.max(info.min, Math.round((t + by) / info.step) * info.step))
        send.restart()
    }
    Timer {     // wait until the clicking stops, then send the new temperature once
        id: send
        interval: 1500
        onTriggered: if (!isNaN(root.pending)) root.run("kantan-home set " + root.pending)
    }
    Timer { id: later; interval: 3000; onTriggered: { root.pending = NaN; root.refresh() } }
    Timer { interval: 60 * 1000; running: true; repeat: true; onTriggered: if (isNaN(root.pending)) root.refresh() }
    Component.onCompleted: refresh()
    onExpandedChanged: if (expanded) refresh()

    // ---- in the bar ----------------------------------------------------------------------
    compactRepresentation: MouseArea {
        Layout.minimumWidth: row.implicitWidth
        Layout.preferredWidth: row.implicitWidth
        onClicked: root.expanded = !root.expanded
        RowLayout {
            id: row
            anchors.fill: parent
            spacing: Kirigami.Units.smallSpacing
            Kirigami.Icon {
                Layout.preferredHeight: parent.height
                Layout.preferredWidth: parent.height
                source: Plasmoid.icon
                opacity: root.ok ? 1 : 0.5
            }
            PC.Label {
                text: root.ok ? root.deg(root.info.current) : root.info.state === "loading" ? "" : "?"
                visible: text !== ""
            }
        }
    }

    // ---- the pop-up ------------------------------------------------------------------------
    fullRepresentation: ColumnLayout {
        Layout.preferredWidth: Kirigami.Units.gridUnit * 20
        Layout.preferredHeight: Kirigami.Units.gridUnit * 18
        spacing: Kirigami.Units.largeSpacing

        PC.Label {
            text: root.ok ? root.info.name : i18n("Smart home")
            font.bold: true
            font.pointSize: Kirigami.Theme.defaultFont.pointSize * 1.2
        }

        // Inside now
        RowLayout {
            visible: root.ok
            spacing: Kirigami.Units.largeSpacing
            Kirigami.Icon {
                Layout.preferredWidth: Kirigami.Units.iconSizes.huge
                Layout.preferredHeight: Kirigami.Units.iconSizes.huge
                source: Plasmoid.icon
            }
            ColumnLayout {
                PC.Label {
                    text: root.ok ? root.deg(root.info.current) : ""
                    font.pointSize: Kirigami.Theme.defaultFont.pointSize * 2.6
                }
                PC.Label {
                    opacity: 0.7
                    text: i18n("Inside now") + (root.ok && root.info.humidity ? " · " + i18n("humidity %1%", Math.round(root.info.humidity)) : "")
                }
            }
        }

        // − Heating to 21° +
        RowLayout {
            visible: root.ok
            Layout.fillWidth: true
            PC.Button {
                visible: root.single
                text: "−"
                font.pointSize: Kirigami.Theme.defaultFont.pointSize * 2
                Layout.preferredWidth: Kirigami.Units.gridUnit * 3
                Layout.preferredHeight: Kirigami.Units.gridUnit * 3
                onClicked: root.nudge(-root.info.step)
                PC.ToolTip.text: i18n("Cooler")
                PC.ToolTip.visible: hovered
            }
            PC.Label {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                text: root.summary
                font.pointSize: Kirigami.Theme.defaultFont.pointSize * 1.4
            }
            PC.Button {
                visible: root.single
                text: "+"
                font.pointSize: Kirigami.Theme.defaultFont.pointSize * 2
                Layout.preferredWidth: Kirigami.Units.gridUnit * 3
                Layout.preferredHeight: Kirigami.Units.gridUnit * 3
                onClicked: root.nudge(root.info.step)
                PC.ToolTip.text: i18n("Warmer")
                PC.ToolTip.visible: hovered
            }
        }

        // Heat / Off (whatever the thermostat offers) and Eco
        RowLayout {
            visible: root.ok
            Layout.alignment: Qt.AlignHCenter
            Repeater {
                model: root.ok ? root.info.modes : []
                delegate: PC.Button {
                    text: root.modeName(modelData)
                    checkable: true
                    checked: root.info.mode === modelData
                    onClicked: { checked = true; root.run("kantan-home mode " + modelData) }
                }
            }
            PC.Button {
                readonly property string eco: root.ok ? (root.info.presets.find(p => p.toLowerCase() === "eco") || "") : ""
                readonly property string none: root.ok ? (root.info.presets.find(p => p.toLowerCase() === "none") || "none") : "none"
                visible: eco !== ""
                text: i18n("Eco")
                icon.name: "battery-profile-powersave"
                checkable: true
                checked: root.ok && root.info.preset === eco
                onClicked: root.run("kantan-home preset " + (checked ? eco : none))
            }
        }

        // Not working yet: say why, and offer the one thing that fixes it
        PC.Label {
            visible: !root.ok
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: root.message
        }
        PC.Button {
            visible: !root.ok && root.info.state !== "loading"
            text: root.info.state === "signed_out" ? i18n("Sign in again")
                : root.info.state === "offline" ? i18n("Try again") : i18n("Set up Smart home")
            icon.name: root.info.state === "offline" ? "view-refresh" : "configure"
            onClicked: {
                if (root.info.state === "offline") root.refresh()
                else { root.expanded = false; root.run("kantan-home") }
            }
        }

        Item { Layout.fillHeight: true }

        RowLayout {
            Layout.fillWidth: true
            PC.Label { text: i18n("Through Home Assistant"); opacity: 0.5; font.pointSize: Kirigami.Theme.smallFont.pointSize }
            Item { Layout.fillWidth: true }
            PC.ToolButton {
                visible: root.info.url !== undefined && root.info.url !== ""
                text: i18n("Open Home Assistant")
                icon.name: "internet-web-browser"
                onClicked: { root.expanded = false; root.run("kantan-home open") }
            }
        }
    }
}
