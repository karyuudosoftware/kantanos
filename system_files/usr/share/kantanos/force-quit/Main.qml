// KantanOS Force Quit window. Data and actions come from "backend" (/usr/libexec/kantanos/force-quit).
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

ApplicationWindow {
    id: win
    visible: true
    title: backend.text.title
    width: Kirigami.Units.gridUnit * 24
    height: Kirigami.Units.gridUnit * 22
    minimumWidth: Kirigami.Units.gridUnit * 18
    minimumHeight: Kirigami.Units.gridUnit * 14

    property string selected: ""
    property string selectedName: ""

    Shortcut { sequence: "Escape"; onActivated: confirm.visible ? confirm.close() : Qt.quit() }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Kirigami.Units.largeSpacing * 2
        spacing: Kirigami.Units.largeSpacing

        Label {
            Layout.fillWidth: true
            text: backend.text.hint
            wrapMode: Text.WordWrap
        }

        Frame {
            Layout.fillWidth: true
            Layout.fillHeight: true
            padding: 1

            ListView {
                id: list
                anchors.fill: parent
                clip: true
                model: backend.apps
                currentIndex: -1
                focus: true
                keyNavigationEnabled: true
                onCurrentIndexChanged: {
                    if (currentIndex >= 0 && currentIndex < count) {
                        win.selected = backend.apps[currentIndex].id
                        win.selectedName = backend.apps[currentIndex].name
                    }
                }
                Connections {
                    target: backend
                    function onAppsChanged() {
                        // keep the same app selected when the list refreshes
                        list.currentIndex = -1
                        for (let i = 0; i < backend.apps.length; i++)
                            if (backend.apps[i].id === win.selected) list.currentIndex = i
                        if (list.currentIndex < 0) { win.selected = ""; win.selectedName = "" }
                    }
                }
                delegate: ItemDelegate {
                    required property var modelData
                    required property int index
                    width: ListView.view.width
                    highlighted: ListView.isCurrentItem
                    onClicked: list.currentIndex = index
                    onDoubleClicked: { list.currentIndex = index; confirm.open() }
                    Keys.onReturnPressed: if (win.selected !== "") confirm.open()
                    contentItem: RowLayout {
                        spacing: Kirigami.Units.largeSpacing
                        Kirigami.Icon {
                            source: modelData.icon
                            Layout.preferredWidth: Kirigami.Units.iconSizes.medium
                            Layout.preferredHeight: Kirigami.Units.iconSizes.medium
                        }
                        Label {
                            Layout.fillWidth: true
                            text: modelData.name
                            elide: Text.ElideRight
                        }
                    }
                }
                Label {
                    anchors.centerIn: parent
                    visible: list.count === 0
                    text: backend.text.none
                    opacity: 0.7
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            Button { text: backend.text.cancel; onClicked: Qt.quit() }
            Button {
                text: backend.text.quit
                icon.name: "process-stop"
                enabled: win.selected !== ""
                highlighted: true
                onClicked: confirm.open()
            }
        }
    }

    Dialog {
        id: confirm
        anchors.centerIn: parent
        modal: true
        title: backend.text.title
        width: Math.min(win.width - Kirigami.Units.gridUnit * 2, Kirigami.Units.gridUnit * 20)
        Label {
            width: parent.width
            wrapMode: Text.WordWrap
            text: backend.text.confirm.replace("%1", win.selectedName)
        }
        footer: DialogButtonBox {
            Button { text: backend.text.no; DialogButtonBox.buttonRole: DialogButtonBox.RejectRole }
            Button { id: yesButton; text: backend.text.yes; highlighted: true; DialogButtonBox.buttonRole: DialogButtonBox.AcceptRole }
        }
        // Enter confirms, Escape cancels
        onOpened: yesButton.forceActiveFocus()
        Shortcut { sequences: ["Return", "Enter"]; enabled: confirm.visible; onActivated: confirm.accept() }
        onAccepted: backend.forceQuit(win.selected)
    }
}
