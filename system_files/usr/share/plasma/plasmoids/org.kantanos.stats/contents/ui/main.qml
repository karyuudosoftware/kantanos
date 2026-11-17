/*
 * KantanOS Stats: the PC's vital signs in the top bar.
 *
 * In the bar: small graphs (or bars, or just numbers) for the processor, graphics card,
 * memory, drive and network; which ones and the style are in the widget's settings.
 * Click for details: gauges, history, each processor core, the busiest apps, every drive.
 * Numbers come from KDE's system statistics service (ksystemstats, which also reads NVIDIA
 * cards); drive space and the app lists come from df, top and ps. Nothing leaves the PC.
 */
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PC
import org.kde.plasma.extras as PlasmaExtras
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami
import org.kde.ksysguard.sensors as Sensors

PlasmoidItem {
    id: root

    readonly property var cfg: Plasmoid.configuration
    readonly property string barStyle: cfg.style || "graph"
    property real barHeight: 26         // the top bar's thickness; item sizes follow it

    // ---- colours -------------------------------------------------------------------------
    readonly property color cpuColor: "#3d8bfd"
    readonly property color gpuColor: "#2fb67c"
    readonly property color memColor: "#a970ff"
    readonly property color diskColor: "#f0a030"
    readonly property color downColor: "#3d8bfd"
    readonly property color upColor: "#ff6b8b"
    function load(color, pct) {     // turns orange, then red, when something is working hard
        return pct >= 90 ? "#e5484d" : pct >= 75 ? "#f08c30" : color
    }

    // ---- numbers -------------------------------------------------------------------------
    function num(v) { return (typeof v === "number" && isFinite(v)) ? v : 0 }
    function pct(v) { return Math.round(num(v)) + "%" }
    function bytes(b, digits) {
        b = num(b)
        var units = ["B", "KB", "MB", "GB", "TB"], i = 0
        while (b >= 1024 && i < units.length - 1) { b /= 1024; i++ }
        var d = digits === undefined ? (b < 10 && i > 0 ? 1 : 0) : digits
        return b.toFixed(d) + " " + units[i]
    }
    function speed(b) { return bytes(b) + "/s" }
    function duration(s) {
        s = Math.floor(num(s))
        var d = Math.floor(s / 86400), h = Math.floor(s % 86400 / 3600), m = Math.floor(s % 3600 / 60)
        if (d > 0) return i18np("1 day", "%1 days", d) + ", " + h + " h"
        if (h > 0) return h + " h " + m + " min"
        return m + " min"
    }

    // ---- sensors (KDE system statistics) --------------------------------------------------
    Sensors.Sensor { id: cpuUsage; sensorId: "cpu/all/usage" }
    Sensors.Sensor { id: cpuUser; sensorId: "cpu/all/user" }
    Sensors.Sensor { id: cpuSystem; sensorId: "cpu/all/system" }
    Sensors.Sensor { id: cpuWait; sensorId: "cpu/all/wait" }
    Sensors.Sensor { id: cpuFreq; sensorId: "cpu/all/averageFrequency" }
    Sensors.Sensor { id: cpuTemp; sensorId: "cpu/all/averageTemperature" }
    Sensors.Sensor { id: load1; sensorId: "cpu/loadaverages/loadaverage1" }
    Sensors.Sensor { id: load5; sensorId: "cpu/loadaverages/loadaverage5" }
    Sensors.Sensor { id: load15; sensorId: "cpu/loadaverages/loadaverage15" }

    Sensors.Sensor { id: gpuUsage; sensorId: "gpu/gpu1/usage" }
    Sensors.Sensor { id: gpuName; sensorId: "gpu/gpu1/name" }
    Sensors.Sensor { id: gpuVramUsed; sensorId: "gpu/gpu1/usedVram" }
    Sensors.Sensor { id: gpuVramTotal; sensorId: "gpu/gpu1/totalVram" }
    Sensors.Sensor { id: gpuTemp; sensorId: "gpu/gpu1/temperature" }
    Sensors.Sensor { id: gpuPower; sensorId: "gpu/gpu1/power" }
    Sensors.Sensor { id: gpuFreq; sensorId: "gpu/gpu1/coreFrequency" }

    Sensors.Sensor { id: memUsedPct; sensorId: "memory/physical/usedPercent" }
    Sensors.Sensor { id: memUsed; sensorId: "memory/physical/used" }
    Sensors.Sensor { id: memTotal; sensorId: "memory/physical/total" }
    Sensors.Sensor { id: memApps; sensorId: "memory/physical/application" }
    Sensors.Sensor { id: memCache; sensorId: "memory/physical/cache" }
    Sensors.Sensor { id: memBuffer; sensorId: "memory/physical/buffer" }
    Sensors.Sensor { id: memFree; sensorId: "memory/physical/free" }     // free + cache that can be handed back
    Sensors.Sensor { id: swapUsed; sensorId: "memory/swap/used" }
    Sensors.Sensor { id: swapTotal; sensorId: "memory/swap/total" }

    Sensors.Sensor { id: diskRead; sensorId: "disk/all/read" }
    Sensors.Sensor { id: diskWrite; sensorId: "disk/all/write" }

    Sensors.Sensor { id: netDown; sensorId: "network/all/download" }
    Sensors.Sensor { id: netUp; sensorId: "network/all/upload" }
    Sensors.Sensor { id: netTotalDown; sensorId: "network/all/totalDownload" }
    Sensors.Sensor { id: netTotalUp; sensorId: "network/all/totalUpload" }

    Sensors.Sensor { id: uptime; sensorId: "os/system/uptime" }

    readonly property bool hasGpu: typeof gpuUsage.value === "number" || num(gpuVramTotal.value) > 0
    readonly property bool hasTemp: num(cpuTemp.value) > 0
    readonly property real memSystem: Math.max(0, num(memUsed.value) - num(memApps.value))   // kernel, drivers
    readonly property real memCached: num(memCache.value) + num(memBuffer.value)
    readonly property real vramPct: num(gpuVramTotal.value) > 0 ? 100 * num(gpuVramUsed.value) / num(gpuVramTotal.value) : 0

    // ---- history (one point a second, two minutes kept) ------------------------------------
    property var cpuHist: []
    property var gpuHist: []
    property var memHist: []
    property var downHist: []
    property var upHist: []
    property var readHist: []
    property var writeHist: []
    function push(list, v) {
        var l = list.slice(Math.max(0, list.length - 119))
        l.push(num(v))
        return l
    }
    Timer {
        interval: 1000; running: true; repeat: true; triggeredOnStart: true
        onTriggered: {
            root.cpuHist = root.push(root.cpuHist, cpuUsage.value)
            root.gpuHist = root.push(root.gpuHist, gpuUsage.value)
            root.memHist = root.push(root.memHist, memUsedPct.value)
            root.downHist = root.push(root.downHist, netDown.value)
            root.upHist = root.push(root.upHist, netUp.value)
            root.readHist = root.push(root.readHist, diskRead.value)
            root.writeHist = root.push(root.writeHist, diskWrite.value)
        }
    }

    // ---- drives and busy apps (small shell commands) ---------------------------------------
    readonly property string dfCommand: "df -B1 --output=source,size,used,target -x tmpfs -x devtmpfs -x overlay "
        + "-x composefs -x efivarfs -x squashfs -x erofs -x fuse -x fuse.portal -x fuse.kio-fuse -x fuse.gvfsd-fuse "
        + "-x fuse.sshfs -x fuse.rclone -x cifs -x smb3 -x nfs -x nfs4 -x autofs 2>/dev/null | tail -n +2"
    readonly property string topCommand: "top -b -n 2 -d 0.7 -w 512 -o %CPU 2>/dev/null"
        + " | awk '/^top -/{n++} n==2 && $1 ~ /^[0-9]+$/ {print $9 \"\\t\" $12}' | head -5;"
        + " echo ==; ps -eo rss=,comm= --sort=-rss | head -5"
    readonly property string infoCommand: "nproc; lscpu -p=core,socket 2>/dev/null | grep -v '^#' | sort -u | wc -l;"
        + " sed -n 's/^model name[^:]*: *//p' /proc/cpuinfo | head -1"
    property int threads: 1
    property int cores: 1
    property string processorName: ""
    property var drives: []          // [{name, size, used}]
    property var mainDrive: null
    property var busyApps: []        // [{name, cpu}]
    property var bigApps: []         // [{name, mem}]

    function driveName(targets) {
        for (var i = 0; i < targets.length; i++)
            if (["/", "/etc", "/usr", "/var", "/sysroot", "/home", "/var/home"].indexOf(targets[i]) >= 0)
                return i18n("KantanOS (this drive)")
        var t = targets[0]
        return t.substring(t.lastIndexOf("/") + 1) || t
    }
    function readDrives(text) {
        var bySource = {}, order = []
        text.split("\n").forEach(function(line) {
            var f = line.trim().split(/\s+/)
            if (f.length < 4) return
            var target = f.slice(3).join(" ")
            var size = parseFloat(f[1]), used = parseFloat(f[2])
            if (!(size > 1e9) || target.indexOf("/boot") === 0) return
            if (!bySource[f[0]]) { bySource[f[0]] = { size: size, used: used, targets: [] }; order.push(f[0]) }
            bySource[f[0]].targets.push(target)
        })
        var list = order.map(function(s) {
            var d = bySource[s]
            return { name: driveName(d.targets), size: d.size, used: d.used }
        })
        list.sort(function(a, b) { return (b.name === i18n("KantanOS (this drive)")) - (a.name === i18n("KantanOS (this drive)")) })
        drives = list
        mainDrive = list.length ? list[0] : null
    }
    function readApps(text) {
        var parts = text.split("==")
        var threads = Math.max(1, root.threads)
        var hidden = /^(kworker|ksoftirqd|rcu_|migration|irq\/|kthreadd|top$)/
        busyApps = (parts[0] || "").split("\n").filter(function(l) {
            return l.trim() !== "" && !hidden.test((l.split("\t")[1] || "").trim())
        }).map(function(l) {
            var f = l.split("\t")
            return { name: (f[1] || "").trim(), cpu: parseFloat(f[0]) / threads }
        })
        bigApps = (parts[1] || "").split("\n").filter(function(l) { return l.trim() !== "" }).map(function(l) {
            var f = l.trim().split(/\s+/)
            return { name: f.slice(1).join(" "), mem: parseFloat(f[0]) * 1024 }
        })
    }

    P5Support.DataSource {
        id: shell
        engine: "executable"
        onNewData: (source, data) => {
            disconnectSource(source)
            if (source === root.dfCommand) root.readDrives(data.stdout || "")
            else if (source === root.topCommand) root.readApps(data.stdout || "")
            else if (source === root.infoCommand) {
                var f = (data.stdout || "").split("\n")
                root.threads = Math.max(1, parseInt(f[0]) || 1)
                root.cores = Math.max(1, parseInt(f[1]) || root.threads)
                root.processorName = (f[2] || "").replace(/\s+/g, " ").replace(/ (\d+-Core )?Processor$/, "").trim()
            }
        }
        function run(cmd) { if (connectedSources.indexOf(cmd) < 0) connectSource(cmd) }
    }
    Timer {
        interval: 30 * 1000; running: true; repeat: true; triggeredOnStart: true
        onTriggered: shell.run(root.dfCommand)
    }
    Timer {
        interval: 3000; running: root.expanded; repeat: true; triggeredOnStart: true
        onTriggered: shell.run(root.topCommand)
    }
    onExpandedChanged: if (expanded) shell.run(root.dfCommand)
    Component.onCompleted: shell.run(root.infoCommand)

    readonly property real diskPct: mainDrive ? 100 * mainDrive.used / mainDrive.size : 0

    toolTipMainText: i18n("System stats")
    toolTipSubText: i18n("Processor %1 · Memory %2", pct(cpuUsage.value), pct(memUsedPct.value))
        + (hasGpu ? " · " + i18n("Graphics %1", pct(gpuUsage.value)) : "")

    // =======================================================================================
    // In the top bar
    // =======================================================================================

    // One item: (graph | bar) + a tiny name over the value
    component BarItem: RowLayout {
        id: item
        property string label
        property string value
        property string widest: "100%"
        property var history: []
        property real fraction: 0
        property color tint: Kirigami.Theme.highlightColor
        spacing: Math.round(Kirigami.Units.smallSpacing * 1.5)
        Layout.fillHeight: true

        Spark {
            visible: root.barStyle === "graph"
            Layout.alignment: Qt.AlignVCenter
            Layout.preferredWidth: Math.round(root.barHeight * 1.25)
            Layout.preferredHeight: Math.round(root.barHeight * 0.62)
            values: item.history
            color: item.tint
            capacity: 24
        }
        Rectangle {
            visible: root.barStyle === "bar"
            Layout.alignment: Qt.AlignVCenter
            Layout.preferredWidth: Math.max(4, Math.round(root.barHeight * 0.17))
            Layout.preferredHeight: Math.round(root.barHeight * 0.62)
            radius: 2
            color: Qt.alpha(Kirigami.Theme.textColor, 0.12)
            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: parent.height * Math.max(0, Math.min(1, item.fraction))
                radius: 2
                color: item.tint
                Behavior on height { NumberAnimation { duration: 300 } }
            }
        }
        ColumnLayout {
            Layout.alignment: Qt.AlignVCenter
            spacing: -Math.round(root.barHeight * 0.04)
            PC.Label {
                text: item.label
                font.pixelSize: Math.max(7, Math.round(root.barHeight * 0.25))
                font.weight: Font.Bold
                font.letterSpacing: 0.6
                opacity: 0.6
            }
            PC.Label {
                id: valueLabel
                text: item.value
                font.pixelSize: Math.max(9, Math.round(root.barHeight * 0.40))
                font.weight: Font.DemiBold
                font.features: { "tnum": 1 }
                Layout.minimumWidth: Math.ceil(widthOf.advanceWidth)   // no jiggling as numbers change
                TextMetrics { id: widthOf; font: valueLabel.font; text: item.widest }
            }
        }
    }

    compactRepresentation: MouseArea {
        id: compact
        Layout.minimumWidth: strip.implicitWidth + Kirigami.Units.smallSpacing * 2
        Layout.preferredWidth: Layout.minimumWidth
        hoverEnabled: true
        onClicked: root.expanded = !root.expanded
        onHeightChanged: if (height > 0) root.barHeight = height

        Rectangle {
            anchors.fill: parent
            anchors.topMargin: 3; anchors.bottomMargin: 3
            radius: 6
            color: Qt.alpha(Kirigami.Theme.textColor, compact.containsMouse || root.expanded ? 0.08 : 0)
        }

        RowLayout {
            id: strip
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: Kirigami.Units.largeSpacing

            BarItem {
                visible: root.cfg.showCpu
                label: "CPU"; value: root.pct(cpuUsage.value)
                history: root.cpuHist; fraction: root.num(cpuUsage.value) / 100
                tint: root.load(root.cpuColor, root.num(cpuUsage.value))
            }
            BarItem {
                visible: root.cfg.showGpu && root.hasGpu
                label: "GPU"; value: root.pct(gpuUsage.value)
                history: root.gpuHist; fraction: root.num(gpuUsage.value) / 100
                tint: root.load(root.gpuColor, root.num(gpuUsage.value))
            }
            BarItem {
                visible: root.cfg.showMemory
                label: "RAM"; value: root.pct(memUsedPct.value)
                history: root.memHist; fraction: root.num(memUsedPct.value) / 100
                tint: root.load(root.memColor, root.num(memUsedPct.value))
            }
            BarItem {
                visible: root.cfg.showDisk && root.mainDrive !== null
                label: "SSD"; value: root.pct(root.diskPct)
                history: root.readHist.map(function(v, i) { return v + (root.writeHist[i] || 0) })
                fraction: root.diskPct / 100
                tint: root.load(root.diskColor, root.diskPct)
            }
            BarItem {
                visible: root.cfg.showTemperature && root.hasTemp
                label: "TEMP"; value: Math.round(root.num(cpuTemp.value)) + "°"; widest: "100°"
                history: []; fraction: root.num(cpuTemp.value) / 100
                tint: root.load("#2fb6c9", root.num(cpuTemp.value) + 5)
            }
            // Network: up and down speeds on two lines, like a status-bar meter
            RowLayout {
                id: net
                visible: root.cfg.showNetwork
                Layout.fillHeight: true
                spacing: Math.round(Kirigami.Units.smallSpacing * 1.5)
                Spark {
                    visible: root.barStyle === "graph"
                    Layout.alignment: Qt.AlignVCenter
                    Layout.preferredWidth: Math.round(root.barHeight * 1.25)
                    Layout.preferredHeight: Math.round(root.barHeight * 0.62)
                    values: root.downHist; values2: root.upHist
                    color: root.downColor; color2: root.upColor
                    maximum: 0; capacity: 24
                }
                ColumnLayout {
                    Layout.alignment: Qt.AlignVCenter
                    spacing: -Math.round(root.barHeight * 0.06)
                    Repeater {
                        model: [ { arrow: "↑", v: netUp.value, c: root.upColor }, { arrow: "↓", v: netDown.value, c: root.downColor } ]
                        RowLayout {
                            spacing: 2
                            PC.Label {
                                text: modelData.arrow
                                color: modelData.c
                                font.pixelSize: Math.max(8, Math.round(root.barHeight * 0.30))
                                font.weight: Font.Bold
                            }
                            PC.Label {
                                id: speedLabel
                                text: root.speed(modelData.v)
                                font.pixelSize: Math.max(8, Math.round(root.barHeight * 0.30))
                                font.weight: Font.DemiBold
                                font.features: { "tnum": 1 }
                                Layout.minimumWidth: Math.ceil(netWidth.advanceWidth)
                                TextMetrics { id: netWidth; font: speedLabel.font; text: "999 KB/s" }
                            }
                        }
                    }
                }
            }
            PC.Label {      // everything switched off: still something to click
                visible: !root.cfg.showCpu && !root.cfg.showGpu && !root.cfg.showMemory
                         && !root.cfg.showDisk && !root.cfg.showNetwork && !root.cfg.showTemperature
                text: "📊"
            }
        }
    }

    // =======================================================================================
    // The pop-up
    // =======================================================================================

    component Section: ColumnLayout {
        id: sec
        property string title
        property string icon
        property string summary
        default property alias content: body.data
        spacing: Kirigami.Units.smallSpacing
        Layout.fillWidth: true
        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: Kirigami.Units.largeSpacing
            Kirigami.Icon { source: sec.icon; Layout.preferredWidth: Kirigami.Units.iconSizes.small; Layout.preferredHeight: Layout.preferredWidth }
            PlasmaExtras.Heading { level: 4; text: sec.title; Layout.fillWidth: true; elide: Text.ElideRight }
            PC.Label { text: sec.summary; opacity: 0.7; font.features: { "tnum": 1 } }
        }
        ColumnLayout { id: body; Layout.fillWidth: true; spacing: Kirigami.Units.smallSpacing }
    }

    component Stat: RowLayout {
        property string name
        property string value
        property color dot: "transparent"
        Layout.fillWidth: true
        Rectangle { visible: dot.a > 0; width: 8; height: 8; radius: 4; color: dot }
        PC.Label { text: name; opacity: 0.75; Layout.fillWidth: true; elide: Text.ElideRight }
        PC.Label { text: value; font.features: { "tnum": 1 } }
    }

    component Meter: Rectangle {      // a thin horizontal bar
        property real fraction: 0
        property color tint: Kirigami.Theme.highlightColor
        Layout.fillWidth: true
        implicitHeight: 6
        radius: 3
        color: Qt.alpha(Kirigami.Theme.textColor, 0.10)
        Rectangle {
            width: parent.width * Math.max(0, Math.min(1, parent.fraction))
            height: parent.height
            radius: 3
            color: parent.tint
            Behavior on width { NumberAnimation { duration: 300 } }
        }
    }

    fullRepresentation: PlasmaExtras.Representation {
        id: full
        Layout.preferredWidth: Kirigami.Units.gridUnit * 26
        Layout.preferredHeight: Kirigami.Units.gridUnit * 36
        Layout.minimumWidth: Kirigami.Units.gridUnit * 20
        Layout.minimumHeight: Kirigami.Units.gridUnit * 20
        collapseMarginsHint: true

        header: PlasmaExtras.PlasmoidHeading {
            RowLayout {
                anchors.fill: parent
                PlasmaExtras.Heading { level: 3; text: i18n("System stats"); Layout.fillWidth: true; Layout.leftMargin: Kirigami.Units.smallSpacing }
                PC.Label { text: i18n("On for %1", root.duration(uptime.value)); opacity: 0.7 }
                PC.ToolButton {
                    icon.name: "configure"
                    display: PC.AbstractButton.IconOnly
                    text: i18n("Choose what the top bar shows")
                    PC.ToolTip.text: text; PC.ToolTip.visible: hovered
                    onClicked: Plasmoid.internalAction("configure").trigger()
                }
            }
        }

        PC.ScrollView {
            id: scroll
            anchors.fill: parent
            contentWidth: availableWidth
            PC.ScrollBar.horizontal.policy: PC.ScrollBar.AlwaysOff

            ColumnLayout {
                width: scroll.availableWidth - Kirigami.Units.largeSpacing * 2
                x: Kirigami.Units.largeSpacing
                spacing: Kirigami.Units.smallSpacing

                // ---- gauges -------------------------------------------------------------
                RowLayout {
                    Layout.fillWidth: true
                    Layout.topMargin: Kirigami.Units.largeSpacing
                    Item { Layout.fillWidth: true }
                    Ring { Layout.alignment: Qt.AlignTop; label: i18n("Processor"); value: root.num(cpuUsage.value); color: root.load(root.cpuColor, value)
                           detail: root.hasTemp ? Math.round(root.num(cpuTemp.value)) + " °C" : "" }
                    Item { Layout.fillWidth: true }
                    Ring { Layout.alignment: Qt.AlignTop; visible: root.hasGpu; label: i18n("Graphics"); value: root.num(gpuUsage.value); color: root.load(root.gpuColor, value)
                           detail: root.num(gpuTemp.value) > 0 ? Math.round(root.num(gpuTemp.value)) + " °C" : "" }
                    Item { visible: root.hasGpu; Layout.fillWidth: true }
                    Ring { Layout.alignment: Qt.AlignTop; label: i18n("Memory"); value: root.num(memUsedPct.value); color: root.load(root.memColor, value)
                           detail: root.bytes(memUsed.value) }
                    Item { Layout.fillWidth: true }
                    Ring { Layout.alignment: Qt.AlignTop; visible: root.mainDrive !== null; label: i18n("Drive"); value: root.diskPct; color: root.load(root.diskColor, value)
                           detail: root.mainDrive ? i18n("%1 free", root.bytes(root.mainDrive.size - root.mainDrive.used)) : "" }
                    Item { Layout.fillWidth: true }
                }

                // ---- processor ----------------------------------------------------------
                Section {
                    title: i18n("Processor")
                    icon: "cpu"
                    summary: root.pct(cpuUsage.value)
                    PC.Label {
                        text: root.processorName
                        visible: text !== ""
                        opacity: 0.6
                        font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                    }
                    Spark {
                        Layout.fillWidth: true
                        Layout.preferredHeight: Kirigami.Units.gridUnit * 3.5
                        values: root.cpuHist; capacity: 120
                        color: root.cpuColor
                    }
                    // one bar per processor thread
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.preferredHeight: Kirigami.Units.gridUnit * 2
                        spacing: 2
                        Repeater {
                            model: Math.min(64, root.threads)
                            Item {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                Sensors.Sensor { id: core; sensorId: "cpu/cpu" + index + "/usage" }
                                Rectangle { anchors.fill: parent; radius: 2; color: Qt.alpha(Kirigami.Theme.textColor, 0.08) }
                                Rectangle {
                                    anchors.bottom: parent.bottom
                                    width: parent.width
                                    height: parent.height * Math.max(0.02, Math.min(1, root.num(core.value) / 100))
                                    radius: 2
                                    color: root.load(root.cpuColor, root.num(core.value))
                                    Behavior on height { NumberAnimation { duration: 300 } }
                                }
                            }
                        }
                    }
                    Stat { name: i18n("Apps"); value: root.pct(cpuUser.value); dot: root.cpuColor }
                    Stat { name: i18n("System"); value: root.pct(cpuSystem.value); dot: "#e5484d" }
                    Stat { name: i18n("Waiting for drives"); value: root.pct(cpuWait.value); dot: "#8b8b8b" }
                    Stat { name: i18n("Speed"); value: (root.num(cpuFreq.value) / 1000).toFixed(2) + " GHz"; visible: root.num(cpuFreq.value) > 0 }
                    Stat { name: i18n("Temperature"); value: Math.round(root.num(cpuTemp.value)) + " °C"; visible: root.hasTemp }
                    Stat { name: i18n("Cores / threads"); value: root.cores + " / " + root.threads }
                    Stat { name: i18n("Load (1, 5, 15 min)"); value: [load1.value, load5.value, load15.value].map(function(v) { return root.num(v).toFixed(2) }).join("  ") }
                    PC.Label { text: i18n("Busiest apps"); font.weight: Font.DemiBold; Layout.topMargin: Kirigami.Units.smallSpacing; visible: root.busyApps.length > 0 }
                    Repeater {
                        model: root.busyApps
                        Stat { name: modelData.name; value: modelData.cpu.toFixed(1) + "%" }
                    }
                }

                // ---- graphics -----------------------------------------------------------
                Section {
                    visible: root.hasGpu
                    title: i18n("Graphics")
                    icon: "video-display"
                    summary: root.pct(gpuUsage.value)
                    PC.Label {
                        text: String(gpuName.value || "")
                        visible: text !== ""
                        opacity: 0.6
                        font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                    }
                    Spark {
                        Layout.fillWidth: true
                        Layout.preferredHeight: Kirigami.Units.gridUnit * 3.5
                        values: root.gpuHist; capacity: 120
                        color: root.gpuColor
                    }
                    Stat { name: i18n("Video memory"); value: root.bytes(gpuVramUsed.value) + " / " + root.bytes(gpuVramTotal.value); visible: root.num(gpuVramTotal.value) > 0 }
                    Meter { fraction: root.vramPct / 100; tint: root.gpuColor; visible: root.num(gpuVramTotal.value) > 0 }
                    Stat { name: i18n("Temperature"); value: Math.round(root.num(gpuTemp.value)) + " °C"; visible: root.num(gpuTemp.value) > 0 }
                    Stat { name: i18n("Power"); value: Math.round(root.num(gpuPower.value)) + " W"; visible: root.num(gpuPower.value) > 0 }
                    Stat { name: i18n("Speed"); value: Math.round(root.num(gpuFreq.value)) + " MHz"; visible: root.num(gpuFreq.value) > 0 }
                }

                // ---- memory -------------------------------------------------------------
                Section {
                    title: i18n("Memory")
                    icon: "memory"
                    summary: root.bytes(memUsed.value) + " / " + root.bytes(memTotal.value)
                    // apps | cache | free, as one bar
                    Item {
                        Layout.fillWidth: true
                        implicitHeight: 10
                        readonly property real total: Math.max(1, root.num(memTotal.value))
                        readonly property real apps: root.num(memApps.value) / total
                        readonly property real sys: root.memSystem / total
                        readonly property real cache: Math.min(1 - apps - sys, root.memCached / total)
                        Rectangle { anchors.fill: parent; radius: 5; color: Qt.alpha(Kirigami.Theme.textColor, 0.10) }
                        Rectangle { id: cacheBar; height: parent.height; radius: 5; width: parent.width * (parent.apps + parent.sys + parent.cache); color: Qt.alpha(root.memColor, 0.3) }
                        Rectangle { id: sysBar; height: parent.height; radius: 5; width: parent.width * (parent.apps + parent.sys); color: "#e5484d" }
                        Rectangle { id: appsBar; height: parent.height; radius: 5; width: parent.width * parent.apps; color: root.memColor }
                    }
                    Stat { name: i18n("Used by apps"); value: root.bytes(memApps.value); dot: root.memColor }
                    Stat { name: i18n("Used by the system"); value: root.bytes(root.memSystem); dot: "#e5484d" }
                    Stat { name: i18n("Cache (handed back when apps need it)"); value: root.bytes(root.memCached); dot: Qt.alpha(root.memColor, 0.3) }
                    Stat { name: i18n("Available for apps"); value: root.bytes(memFree.value) }
                    Stat { name: i18n("Swap"); value: root.bytes(swapUsed.value) + " / " + root.bytes(swapTotal.value); visible: root.num(swapTotal.value) > 0 }
                    PC.Label { text: i18n("Apps using the most memory"); font.weight: Font.DemiBold; Layout.topMargin: Kirigami.Units.smallSpacing; visible: root.bigApps.length > 0 }
                    Repeater {
                        model: root.bigApps
                        Stat { name: modelData.name; value: root.bytes(modelData.mem) }
                    }
                }

                // ---- drives -------------------------------------------------------------
                Section {
                    title: i18n("Drives")
                    icon: "drive-harddisk"
                    summary: "R " + root.speed(diskRead.value) + "   W " + root.speed(diskWrite.value)
                    Spark {
                        Layout.fillWidth: true
                        Layout.preferredHeight: Kirigami.Units.gridUnit * 2.5
                        values: root.readHist; values2: root.writeHist; capacity: 120; maximum: 0
                        color: root.diskColor; color2: "#e5484d"
                    }
                    Repeater {
                        model: root.drives
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            Stat { name: modelData.name; value: i18n("%1 free of %2", root.bytes(modelData.size - modelData.used), root.bytes(modelData.size)) }
                            Meter { fraction: modelData.used / modelData.size; tint: root.load(root.diskColor, 100 * modelData.used / modelData.size) }
                        }
                    }
                }

                // ---- network ------------------------------------------------------------
                Section {
                    title: i18n("Network")
                    icon: "network-wired"
                    summary: "↓ " + root.speed(netDown.value) + "   ↑ " + root.speed(netUp.value)
                    Spark {
                        Layout.fillWidth: true
                        Layout.preferredHeight: Kirigami.Units.gridUnit * 3
                        values: root.downHist; values2: root.upHist; capacity: 120; maximum: 0
                        color: root.downColor; color2: root.upColor
                    }
                    Stat { name: i18n("Downloading"); value: root.speed(netDown.value); dot: root.downColor }
                    Stat { name: i18n("Uploading"); value: root.speed(netUp.value); dot: root.upColor }
                    Stat { name: i18n("Downloaded since the PC started"); value: root.bytes(netTotalDown.value, 1) }
                    Stat { name: i18n("Uploaded since the PC started"); value: root.bytes(netTotalUp.value, 1) }
                }

                PC.Button {
                    Layout.alignment: Qt.AlignHCenter
                    Layout.topMargin: Kirigami.Units.largeSpacing
                    Layout.bottomMargin: Kirigami.Units.largeSpacing
                    icon.name: "utilities-system-monitor"
                    text: i18n("Open System Monitor")
                    onClicked: {
                        shell.run("setsid plasma-systemmonitor >/dev/null 2>&1 &")
                        root.expanded = false
                    }
                }
            }
        }
    }
}
