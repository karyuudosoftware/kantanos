/*
 * KantanOS Dock: a glass bar with the app launcher, pinned and open apps, and the Trash.
 * Icons magnify as the pointer moves along the dock and grow upward out of the bar, like
 * the macOS dock. Built on Plasma's own task list (org.kde.taskmanager), so it knows the
 * same apps and windows as the standard task manager.
 *
 * The dock's panel is see-through (the Kantan Glass theme leaves bottom panels empty), and
 * this widget draws the bar itself along the bottom, leaving room above it for magnified
 * icons.
 *
 *   click          open the app, bring its window forward, or minimize it if it is in front
 *   middle click   open another window of the app
 *   right click    menu: new window, keep in dock / remove, close
 */
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.extras as PlasmaExtras
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami
import org.kde.taskmanager as TaskManager

PlasmoidItem {
    id: root

    preferredRepresentation: fullRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground

    // ---- sizes ---------------------------------------------------------------------------
    readonly property real magnify: Math.max(1, Plasmoid.configuration.magnification)
    readonly property real thickness: Math.max(32, height)
    readonly property real pad: Math.round(thickness * 0.07)          // inside the glass bar
    // Resting icon size: a magnified icon (plus the bar's padding) must fit in the panel.
    readonly property real base: Math.floor((thickness - pad * 2) / magnify)
    readonly property real gap: Math.round(base * 0.22)
    readonly property real cell: base + gap
    readonly property real barHeight: base + pad * 2
    readonly property bool showTrash: Plasmoid.configuration.showTrash
    // tiles: launcher, apps, [separator], trash
    readonly property int tileCount: 1 + tasksModel.count + (showTrash ? 1 : 0)
    readonly property real sepWidth: showTrash ? gap * 2 : 0
    readonly property real restWidth: tileCount * cell + sepWidth
    // Room kept free at both ends for magnified icons, so the dock never changes size (and
    // jumps) while the pointer moves over it.
    readonly property real spare: base * (magnify - 1) * 2.4

    // Pointer position along the dock, or -1 when the pointer is not over it.
    property real pointerX: -1
    readonly property bool magnifying: pointerX >= 0

    function scaleAt(restCenter) {
        if (!magnifying || magnify <= 1)
            return 1
        const d = (pointerX - restCenter) / cell             // distance in icons
        return 1 + (magnify - 1) * Math.exp(-(d * d) / 2.6)   // smooth bell curve
    }

    // ---- task list -----------------------------------------------------------------------
    TaskManager.VirtualDesktopInfo { id: virtualDesktopInfo }
    TaskManager.ActivityInfo { id: activityInfo }

    TaskManager.TasksModel {
        id: tasksModel
        groupMode: TaskManager.TasksModel.GroupApplications
        groupInline: false
        sortMode: TaskManager.TasksModel.SortManual
        separateLaunchers: false
        launchInPlace: true
        hideActivatedLaunchers: true
        filterByVirtualDesktop: false
        filterByScreen: false
        filterByActivity: false
        virtualDesktop: virtualDesktopInfo.currentDesktop
        activity: activityInfo.currentActivity
        screenGeometry: Plasmoid.containment.screenGeometry
        launcherList: Plasmoid.configuration.launchers
        onLauncherListChanged: {
            if (JSON.stringify(launcherList) !== JSON.stringify(Plasmoid.configuration.launchers))
                Plasmoid.configuration.launchers = launcherList
        }
    }

    function idx(row) { return tasksModel.makeModelIndex(row) }

    function activate(row, m) {
        if (m.IsStartup)
            return
        if (m.IsLauncher)
            tasksModel.requestActivate(idx(row))             // starts the app
        else if (m.IsActive && !m.IsGroupParent)
            tasksModel.requestToggleMinimized(idx(row))
        else
            tasksModel.requestActivate(idx(row))
    }

    // Runs a command (used to open the app launcher menu).
    P5Support.DataSource {
        id: run
        engine: "executable"
        connectedSources: []
        onNewData: (source) => disconnectSource(source)
        function exec(cmd) { connectSource(cmd) }
    }
    function openLauncherMenu() {
        run.exec("busctl --user call org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell activateLauncherMenu")
    }

    // ---- one dock tile -------------------------------------------------------------------
    component Tile: Item {
        id: tile
        property real restCenter: 0
        property alias iconSource: icon.source
        property bool running: false
        property bool front: false
        property bool dim: false
        property bool hop: false
        property string tip: ""
        property string tipSub: ""
        signal leftClicked()
        signal middleClicked()
        signal rightClicked()

        readonly property real zoom: root.scaleAt(restCenter)
        width: root.base * zoom + root.gap
        height: parent ? parent.height : 0
        Behavior on width { enabled: !root.magnifying; NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }

        Kirigami.Icon {
            id: icon
            width: root.base * tile.zoom
            height: width
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: root.pad - hopper.offset
            active: area.containsMouse
            opacity: tile.dim ? 0.6 : 1
            Behavior on width { enabled: !root.magnifying; NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }

            QtObject { id: hopper; property real offset: 0 }
            SequentialAnimation {
                running: tile.hop
                loops: Animation.Infinite
                onRunningChanged: if (!running) hopper.offset = 0
                NumberAnimation { target: hopper; property: "offset"; to: root.base * 0.4; duration: 280; easing.type: Easing.OutQuad }
                NumberAnimation { target: hopper; property: "offset"; to: 0; duration: 280; easing.type: Easing.InQuad }
                PauseAnimation { duration: 140 }
            }
        }

        // Running indicator: a dot under the icon, wider when the app is in front
        Rectangle {
            visible: tile.running
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: Math.max(2, Math.round(root.pad * 0.3))
            height: Math.max(4, Math.round(root.base * 0.09))
            width: tile.front ? height * 2.6 : height
            radius: height / 2
            color: Kirigami.Theme.highlightColor
            Behavior on width { NumberAnimation { duration: 150 } }
        }

        PlasmaCore.ToolTipArea {
            anchors.fill: parent
            mainText: tile.tip
            subText: tile.tipSub
            location: Plasmoid.location
        }
        MouseArea {
            id: area
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton
            onClicked: (ev) => {
                if (ev.button === Qt.MiddleButton) tile.middleClicked()
                else if (ev.button === Qt.RightButton) tile.rightClicked()
                else tile.leftClicked()
            }
        }
    }

    // ---- look ----------------------------------------------------------------------------
    fullRepresentation: Item {
        id: dock
        Layout.preferredWidth: root.restWidth + root.spare
        Layout.minimumWidth: root.restWidth + root.spare
        Layout.maximumWidth: root.restWidth + root.spare
        Layout.fillHeight: true

        HoverHandler {
            id: hover
            onPointChanged: root.pointerX = hovered ? point.position.x : -1
            onHoveredChanged: if (!hovered) root.pointerX = -1
        }

        // Left edge of the tiles when nothing is magnified.
        readonly property real restLeft: (width - root.restWidth) / 2
        function restCenterOf(slot, afterSeparator) {
            return restLeft + slot * root.cell + (afterSeparator ? root.sepWidth : 0) + root.cell / 2
        }

        // The glass bar along the bottom
        Rectangle {
            id: bar
            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            width: row.width + root.pad * 2
            height: root.barHeight
            radius: Math.round(height * 0.32)
            color: Qt.alpha(Kirigami.Theme.backgroundColor, 0.62)
            border.width: 1
            border.color: Qt.alpha(Kirigami.Theme.textColor, 0.14)
        }

        Row {
            id: row
            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            height: parent.height

            // App launcher (opens the KantanOS menu)
            Tile {
                restCenter: dock.restCenterOf(0, false)
                iconSource: "kantanos"
                tip: i18n("Applications")
                onLeftClicked: root.openLauncherMenu()
            }

            Repeater {
                model: tasksModel
                delegate: Tile {
                    id: task
                    required property int index
                    required property var model
                    restCenter: dock.restCenterOf(index + 1, false)
                    iconSource: model.decoration
                    running: !model.IsLauncher && !model.IsStartup
                    front: model.IsActive
                    dim: model.IsMinimized
                    hop: model.IsStartup || model.IsDemandingAttention
                    tip: model.AppName || model.display || ""
                    tipSub: model.ChildCount > 1 ? i18n("%1 windows", model.ChildCount)
                          : (!model.IsLauncher && model.display !== model.AppName ? (model.display || "") : "")
                    onLeftClicked: root.activate(index, model)
                    onMiddleClicked: tasksModel.requestNewInstance(root.idx(index))
                    onRightClicked: root.openMenu(task, index, model)

                    // Tell the window manager where this icon is, so minimizing animates into it
                    function publish() {
                        const p = task.mapToGlobal(0, 0)
                        tasksModel.requestPublishDelegateGeometry(root.idx(index), Qt.rect(p.x, p.y, width, height), task)
                    }
                    Timer { id: publishTimer; interval: 300; onTriggered: task.publish() }
                    onXChanged: publishTimer.restart()
                    Component.onCompleted: publishTimer.restart()
                }
            }

            // Separator
            Item {
                visible: root.showTrash
                width: root.sepWidth
                height: row.height
                Rectangle {
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: root.pad + root.base * 0.15
                    width: 1
                    height: root.base * 0.7
                    color: Kirigami.Theme.textColor
                    opacity: 0.25
                }
            }

            // Trash
            Tile {
                visible: root.showTrash
                restCenter: dock.restCenterOf(1 + tasksModel.count, true)
                iconSource: "user-trash"
                tip: i18n("Trash")
                onLeftClicked: Qt.openUrlExternally("trash:/")
            }
        }
    }

    // ---- right-click menu ----------------------------------------------------------------
    property int menuRow: -1
    property string menuLauncher: ""

    function openMenu(visual, row, m) {
        menuRow = row
        menuLauncher = m.LauncherUrlWithoutIcon ? m.LauncherUrlWithoutIcon.toString() : ""
        titleItem.text = m.AppName || m.display || ""
        newWindowItem.visible = !m.IsLauncher
        const pinned = menuLauncher !== "" && tasksModel.launcherPosition(menuLauncher) !== -1
        pinItem.visible = menuLauncher !== "" && !pinned
        unpinItem.visible = pinned
        closeItem.visible = !m.IsLauncher && !m.IsStartup
        contextMenu.visualParent = visual
        contextMenu.openRelative()
    }

    PlasmaExtras.Menu {
        id: contextMenu
        placement: PlasmaExtras.Menu.TopPosedLeftAlignedPopup
        PlasmaExtras.MenuItem { id: titleItem; enabled: false }
        PlasmaExtras.MenuItem { separator: true }
        PlasmaExtras.MenuItem {
            id: newWindowItem
            text: i18n("New Window")
            icon: "window-new"
            onClicked: tasksModel.requestNewInstance(root.idx(root.menuRow))
        }
        PlasmaExtras.MenuItem {
            id: pinItem
            text: i18n("Keep in Dock")
            icon: "window-pin"
            onClicked: tasksModel.requestAddLauncher(root.menuLauncher)
        }
        PlasmaExtras.MenuItem {
            id: unpinItem
            text: i18n("Remove from Dock")
            icon: "window-unpin"
            onClicked: tasksModel.requestRemoveLauncher(root.menuLauncher)
        }
        PlasmaExtras.MenuItem {
            id: closeItem
            text: i18n("Close")
            icon: "window-close"
            onClicked: tasksModel.requestClose(root.idx(root.menuRow))
        }
    }
}
