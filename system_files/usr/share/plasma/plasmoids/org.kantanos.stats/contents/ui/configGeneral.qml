import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami
import org.kde.kcmutils as KCM

KCM.SimpleKCM {
    property alias cfg_showCpu: showCpu.checked
    property alias cfg_showGpu: showGpu.checked
    property alias cfg_showMemory: showMemory.checked
    property alias cfg_showDisk: showDisk.checked
    property alias cfg_showNetwork: showNetwork.checked
    property alias cfg_showTemperature: showTemperature.checked
    property string cfg_style

    Kirigami.FormLayout {
        QQC2.CheckBox { id: showCpu; Kirigami.FormData.label: i18n("Show in the top bar:"); text: i18n("Processor (CPU)") }
        QQC2.CheckBox { id: showGpu; text: i18n("Graphics card (GPU)") }
        QQC2.CheckBox { id: showMemory; text: i18n("Memory (RAM)") }
        QQC2.CheckBox { id: showDisk; text: i18n("Drive space") }
        QQC2.CheckBox { id: showNetwork; text: i18n("Network speed") }
        QQC2.CheckBox { id: showTemperature; text: i18n("Processor temperature") }

        Item { Kirigami.FormData.isSection: true }

        QQC2.ComboBox {
            Kirigami.FormData.label: i18n("Style:")
            textRole: "text"
            valueRole: "value"
            model: [
                { text: i18n("Small graphs"), value: "graph" },
                { text: i18n("Bars"), value: "bar" },
                { text: i18n("Numbers only"), value: "text" }
            ]
            Component.onCompleted: currentIndex = Math.max(0, indexOfValue(cfg_style))
            onActivated: cfg_style = currentValue
        }
    }
}
