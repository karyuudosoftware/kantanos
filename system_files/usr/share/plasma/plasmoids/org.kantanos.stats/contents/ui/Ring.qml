/* A round gauge (0-100) with the value in the middle and a name underneath. */
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PC
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: ring
    property real value: 0
    property color color: Kirigami.Theme.highlightColor
    property string label: ""
    property string detail: ""
    spacing: 2

    onValueChanged: canvas.requestPaint()
    onColorChanged: canvas.requestPaint()

    Item {
        Layout.alignment: Qt.AlignHCenter
        Layout.preferredWidth: Kirigami.Units.gridUnit * 4
        Layout.preferredHeight: Layout.preferredWidth
        Canvas {
            id: canvas
            anchors.fill: parent
            onPaint: {
                var ctx = getContext("2d")
                ctx.reset()
                var lw = Kirigami.Units.gridUnit * 0.4, r = width / 2 - lw
                var start = 0.75 * Math.PI, sweep = 1.5 * Math.PI
                ctx.lineCap = "round"
                ctx.lineWidth = lw
                ctx.strokeStyle = Qt.alpha(Kirigami.Theme.textColor, 0.12)
                ctx.beginPath(); ctx.arc(width / 2, height / 2, r, start, start + sweep); ctx.stroke()
                var f = Math.max(0, Math.min(1, ring.value / 100))
                if (f > 0.005) {
                    ctx.strokeStyle = ring.color
                    ctx.beginPath(); ctx.arc(width / 2, height / 2, r, start, start + sweep * f); ctx.stroke()
                }
            }
        }
        PC.Label {
            anchors.centerIn: parent
            text: Math.round(ring.value) + "%"
            font.pixelSize: Kirigami.Units.gridUnit * 0.95
            font.weight: Font.DemiBold
            font.features: { "tnum": 1 }
        }
    }
    PC.Label {
        Layout.alignment: Qt.AlignHCenter
        text: ring.label
        font.weight: Font.DemiBold
    }
    PC.Label {
        Layout.alignment: Qt.AlignHCenter
        text: ring.detail
        opacity: 0.65
        font.pixelSize: Kirigami.Theme.smallFont.pixelSize
        visible: text !== ""
    }
}
