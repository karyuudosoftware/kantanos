/* A small history graph: newest value on the right. One or two series (network: down + up). */
import QtQuick
import org.kde.kirigami as Kirigami

Item {
    id: spark
    property var values: []
    property var values2: null
    property color color: Kirigami.Theme.highlightColor
    property color color2: Kirigami.Theme.negativeTextColor
    property real maximum: 100          // 0: scale to the largest value shown
    property int capacity: 40           // points across the width
    property bool framed: true
    property real lineWidth: 1.5

    onValuesChanged: canvas.requestPaint()
    onValues2Changed: canvas.requestPaint()
    onWidthChanged: canvas.requestPaint()
    onHeightChanged: canvas.requestPaint()

    Rectangle {
        anchors.fill: parent
        visible: spark.framed
        radius: 3
        color: Qt.alpha(Kirigami.Theme.textColor, 0.07)
        border.width: 1
        border.color: Qt.alpha(Kirigami.Theme.textColor, 0.10)
    }

    Canvas {
        id: canvas
        anchors.fill: parent
        anchors.margins: spark.framed ? 1 : 0
        renderStrategy: Canvas.Cooperative

        function series(ctx, vals, col, max) {
            var n = Math.min(vals.length, spark.capacity)
            if (n < 2) return
            var w = width, h = height, step = w / (spark.capacity - 1)
            var x0 = w - (n - 1) * step
            ctx.beginPath()
            ctx.moveTo(x0, h)
            for (var i = 0; i < n; i++) {
                var v = vals[vals.length - n + i]
                var y = h - Math.max(0, Math.min(1, v / max)) * (h - spark.lineWidth)
                ctx.lineTo(x0 + i * step, y)
            }
            ctx.lineTo(w, h)
            ctx.closePath()
            ctx.fillStyle = Qt.alpha(col, 0.28)
            ctx.fill()
            ctx.beginPath()
            for (var j = 0; j < n; j++) {
                var v2 = vals[vals.length - n + j]
                var y2 = h - Math.max(0, Math.min(1, v2 / max)) * (h - spark.lineWidth)
                if (j === 0) ctx.moveTo(x0, y2); else ctx.lineTo(x0 + j * step, y2)
            }
            ctx.strokeStyle = col
            ctx.lineWidth = spark.lineWidth
            ctx.lineJoin = "round"
            ctx.stroke()
        }

        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            var max = spark.maximum
            if (max <= 0) {
                max = 1
                var all = spark.values.concat(spark.values2 || [])
                for (var i = Math.max(0, all.length - 2 * spark.capacity); i < all.length; i++) max = Math.max(max, all[i])
                max *= 1.15
            }
            if (spark.values2) series(ctx, spark.values2, spark.color2, max)
            series(ctx, spark.values, spark.color, max)
        }
    }
}
