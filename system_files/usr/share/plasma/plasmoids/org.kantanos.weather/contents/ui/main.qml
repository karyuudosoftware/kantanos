/*
 * KantanOS Weather: the weather for one town, from Open-Meteo (free, no account, worldwide).
 *
 * In the bar: an icon and the temperature. Click for now, the next 12 hours and 7 days.
 * Where: the town chosen in the widget; else the PC's location set with
 * "ujust kantan-set-location" (/etc/geolocation); else the location GeoClue finds (nearby
 * Wi-Fi networks, looked up in BeaconDB). Only the town's coordinates are sent to
 * Open-Meteo; the town search sends only what you type.
 */
import QtQuick
import QtQuick.Layouts
import QtPositioning
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PC
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    property var weather: null          // last Open-Meteo answer
    property string status: ""          // message when there is no weather to show
    property var searchResults: []
    property bool searching: false

    readonly property real lat: Plasmoid.configuration.latitude
    readonly property real lon: Plasmoid.configuration.longitude
    readonly property bool hasPlace: !(lat === 0 && lon === 0)
    readonly property bool fahrenheit: Plasmoid.configuration.units === "fahrenheit"
        || (Plasmoid.configuration.units === "auto" && Qt.locale().measurementSystem === Locale.ImperialUSSystem)

    toolTipMainText: weather ? Plasmoid.configuration.placeName || i18n("Weather") : i18n("Weather")
    toolTipSubText: weather ? describe(weather.current.weather_code) + ", " + temp(weather.current.temperature_2m) : status

    // ---- weather codes (WMO) → words and Breeze icons -----------------------------------
    function describe(code) {
        if (code === 0) return i18n("Clear")
        if (code <= 2) return i18n("Partly cloudy")
        if (code === 3) return i18n("Cloudy")
        if (code <= 48) return i18n("Fog")
        if (code <= 57) return i18n("Drizzle")
        if (code <= 67) return i18n("Rain")
        if (code <= 77) return i18n("Snow")
        if (code <= 82) return i18n("Showers")
        if (code <= 86) return i18n("Snow showers")
        return i18n("Thunderstorm")
    }
    function icon(code, day) {
        var night = day === 0
        if (code === 0) return night ? "weather-clear-night" : "weather-clear"
        if (code <= 2) return night ? "weather-few-clouds-night" : "weather-few-clouds"
        if (code === 3) return "weather-overcast"
        if (code <= 48) return "weather-fog"
        if (code <= 57) return "weather-showers-scattered"
        if (code <= 67) return "weather-showers"
        if (code <= 77) return "weather-snow"
        if (code <= 82) return "weather-showers"
        if (code <= 86) return "weather-snow-scattered"
        return "weather-storm"
    }
    function temp(t) { return Math.round(t) + "°" }

    // ---- fetching ---------------------------------------------------------------------
    function get(url, done) {
        var xhr = new XMLHttpRequest()
        xhr.onreadystatechange = function() {
            if (xhr.readyState !== XMLHttpRequest.DONE) return
            if (xhr.status === 200) {
                try { done(JSON.parse(xhr.responseText)); return } catch (e) {}
            }
            done(null)
        }
        xhr.open("GET", url)
        xhr.send()
    }

    function refresh() {
        if (!hasPlace) {
            status = i18n("Choose your town")
            return
        }
        var url = "https://api.open-meteo.com/v1/forecast?latitude=" + lat.toFixed(4) + "&longitude=" + lon.toFixed(4)
            + "&current=temperature_2m,apparent_temperature,weather_code,is_day,wind_speed_10m,relative_humidity_2m"
            + "&hourly=temperature_2m,weather_code,is_day,precipitation_probability"
            + "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
            + "&timezone=auto&forecast_days=7"
            + (fahrenheit ? "&temperature_unit=fahrenheit&wind_speed_unit=mph" : "")
        get(url, function(data) {
            if (data && data.current) {
                weather = data
                status = ""
            } else if (!weather) {
                status = i18n("No weather right now (no internet?)")
            }
        })
    }

    function search(text) {
        if (text.trim().length < 2) return
        searching = true
        get("https://geocoding-api.open-meteo.com/v1/search?count=6&language=" + Qt.locale().name.split("_")[0]
            + "&name=" + encodeURIComponent(text.trim()), function(data) {
            searching = false
            searchResults = (data && data.results) ? data.results : []
        })
    }

    function choose(place) {
        Plasmoid.configuration.latitude = place.latitude
        Plasmoid.configuration.longitude = place.longitude
        Plasmoid.configuration.placeName = place.name
        searchResults = []
        weather = null
        refresh()
    }

    // The PC's location from "ujust kantan-set-location", when the widget has no town yet
    P5Support.DataSource {
        id: shell
        engine: "executable"
        onNewData: (source, data) => {
            disconnectSource(source)
            var lines = (data.stdout || "").split("\n").filter(l => l.trim() !== "" && l.trim()[0] !== "#")
            if (lines.length >= 2 && !root.hasPlace) {
                var la = parseFloat(lines[0]), lo = parseFloat(lines[1])
                if (!isNaN(la) && !isNaN(lo)) {
                    Plasmoid.configuration.latitude = la
                    Plasmoid.configuration.longitude = lo
                    Plasmoid.configuration.placeName = i18n("Home")
                }
            }
            if (root.hasPlace) root.refresh()
            else root.locate()
        }
    }

    // No town and no /etc/geolocation: ask GeoClue once (allowed for plasmashell in
    // /etc/geoclue/conf.d/90-kantanos.conf). Gives up quietly after a minute.
    property bool locating: false
    function locate() {
        locating = true
        status = i18n("Finding where you are…")
        gps.start()
        gpsTimeout.restart()
    }
    function stopLocating() {
        gps.stop()
        gpsTimeout.stop()
        locating = false
        if (!hasPlace) status = i18n("Choose your town")
    }
    PositionSource {
        id: gps
        name: "geoclue2"
        active: false
        preferredPositioningMethods: PositionSource.AllPositioningMethods
        PluginParameter { name: "desktopId"; value: "org.kde.plasmashell" }
        onPositionChanged: {
            var c = position.coordinate
            if (!root.locating || !c.isValid) return
            if (!root.hasPlace) {
                Plasmoid.configuration.latitude = Math.round(c.latitude * 100) / 100     // about 1 km
                Plasmoid.configuration.longitude = Math.round(c.longitude * 100) / 100
                Plasmoid.configuration.placeName = i18n("Your area")
            }
            root.stopLocating()
            root.refresh()
        }
        onSourceErrorChanged: if (sourceError !== PositionSource.NoError && root.locating) root.stopLocating()
    }
    Timer { id: gpsTimeout; interval: 60 * 1000; onTriggered: root.stopLocating() }

    Component.onCompleted: {
        if (hasPlace) refresh()
        else shell.connectSource("cat /etc/geolocation")
    }
    onFahrenheitChanged: refresh()

    Timer {
        interval: 30 * 60 * 1000
        running: true
        repeat: true
        onTriggered: root.refresh()
    }

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
                source: root.weather ? root.icon(root.weather.current.weather_code, root.weather.current.is_day)
                                     : root.hasPlace ? "weather-overcast" : "mark-location"
            }
            PC.Label {
                // Without a town, say so in the bar instead of showing a bare question mark
                text: root.weather ? root.temp(root.weather.current.temperature_2m)
                                   : root.hasPlace ? "" : root.locating ? "…" : i18n("Set town")
                visible: text !== ""
            }
        }
    }

    // ---- the pop-up ------------------------------------------------------------------------
    fullRepresentation: ColumnLayout {
        Layout.preferredWidth: Kirigami.Units.gridUnit * 24
        Layout.preferredHeight: Kirigami.Units.gridUnit * 26
        spacing: Kirigami.Units.largeSpacing

        // Town search (shown when no town is set, or after "Change town")
        ColumnLayout {
            id: picker
            visible: !root.hasPlace || changing
            property bool changing: false
            Layout.fillWidth: true
            PC.Label { text: i18n("Which town?"); font.bold: true }
            PC.TextField {
                id: query
                Layout.fillWidth: true
                placeholderText: i18n("Type a town and press Enter")
                onAccepted: root.search(text)
            }
            PC.BusyIndicator { visible: root.searching; running: visible }
            Repeater {
                model: root.searchResults
                delegate: PC.ItemDelegate {
                    Layout.fillWidth: true
                    text: modelData.name + ", " + [modelData.admin1, modelData.country].filter(x => x).join(", ")
                    onClicked: { picker.changing = false; root.choose(modelData) }
                }
            }
        }

        // Now
        RowLayout {
            visible: root.weather !== null && !picker.visible
            spacing: Kirigami.Units.largeSpacing
            Kirigami.Icon {
                Layout.preferredWidth: Kirigami.Units.iconSizes.huge
                Layout.preferredHeight: Kirigami.Units.iconSizes.huge
                source: root.weather ? root.icon(root.weather.current.weather_code, root.weather.current.is_day) : ""
            }
            ColumnLayout {
                PC.Label {
                    text: root.weather ? root.temp(root.weather.current.temperature_2m) : ""
                    font.pointSize: Kirigami.Theme.defaultFont.pointSize * 2.4
                }
                PC.Label {
                    text: root.weather ? root.describe(root.weather.current.weather_code) + " · "
                        + i18n("feels like %1", root.temp(root.weather.current.apparent_temperature)) : ""
                }
                PC.Label {
                    opacity: 0.7
                    text: root.weather ? Plasmoid.configuration.placeName + " · "
                        + i18n("wind %1 %2", Math.round(root.weather.current.wind_speed_10m), root.fahrenheit ? "mph" : "km/h")
                        + " · " + i18n("humidity %1%", root.weather.current.relative_humidity_2m) : ""
                }
            }
        }

        // Next 12 hours
        RowLayout {
            visible: root.weather !== null && !picker.visible
            Layout.fillWidth: true
            Repeater {
                model: {
                    if (!root.weather) return []
                    var h = root.weather.hourly, out = []
                    var now = root.weather.current.time.substring(0, 13)
                    var start = Math.max(0, h.time.findIndex(t => t.substring(0, 13) >= now))
                    for (var i = start; i < Math.min(h.time.length, start + 12); i += 2)
                        out.push({ hour: h.time[i].substring(11, 16), t: h.temperature_2m[i],
                                   code: h.weather_code[i], day: h.is_day[i], rain: h.precipitation_probability[i] })
                    return out
                }
                delegate: ColumnLayout {
                    Layout.fillWidth: true
                    PC.Label { Layout.alignment: Qt.AlignHCenter; text: modelData.hour; opacity: 0.7 }
                    Kirigami.Icon {
                        Layout.alignment: Qt.AlignHCenter
                        Layout.preferredWidth: Kirigami.Units.iconSizes.medium
                        Layout.preferredHeight: Kirigami.Units.iconSizes.medium
                        source: root.icon(modelData.code, modelData.day)
                    }
                    PC.Label { Layout.alignment: Qt.AlignHCenter; text: root.temp(modelData.t) }
                    PC.Label {
                        Layout.alignment: Qt.AlignHCenter
                        text: modelData.rain >= 20 ? modelData.rain + "%" : " "
                        opacity: 0.7
                    }
                }
            }
        }

        // 7 days
        ColumnLayout {
            visible: root.weather !== null && !picker.visible
            Layout.fillWidth: true
            spacing: 0
            Repeater {
                model: root.weather ? root.weather.daily.time.length : 0
                delegate: RowLayout {
                    required property int index
                    readonly property var d: root.weather.daily
                    Layout.fillWidth: true
                    PC.Label {
                        Layout.preferredWidth: Kirigami.Units.gridUnit * 6
                        text: index === 0 ? i18n("Today")
                            : Qt.locale().dayName(new Date(d.time[index] + "T12:00").getDay(), Locale.LongFormat)
                    }
                    Kirigami.Icon {
                        Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                        Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
                        source: root.icon(d.weather_code[index], 1)
                    }
                    PC.Label {
                        Layout.fillWidth: true
                        text: d.precipitation_probability_max[index] >= 20 ? "  " + d.precipitation_probability_max[index] + "%" : ""
                        opacity: 0.7
                    }
                    PC.Label { text: root.temp(d.temperature_2m_min[index]); opacity: 0.7 }
                    PC.Label { text: root.temp(d.temperature_2m_max[index]); font.bold: true }
                }
            }
        }

        PC.Label {
            visible: root.weather === null && !picker.visible
            text: root.status
        }

        Item { Layout.fillHeight: true }

        RowLayout {
            Layout.fillWidth: true
            PC.Label { text: i18n("Weather: Open-Meteo.com"); opacity: 0.5; font.pointSize: Kirigami.Theme.smallFont.pointSize }
            Item { Layout.fillWidth: true }
            PC.ToolButton {
                text: root.fahrenheit ? "°F → °C" : "°C → °F"
                onClicked: Plasmoid.configuration.units = root.fahrenheit ? "celsius" : "fahrenheit"
            }
            PC.ToolButton {
                visible: root.hasPlace
                text: i18n("Change town")
                icon.name: "mark-location"
                onClicked: { picker.changing = !picker.changing; query.forceActiveFocus() }
            }
        }
    }
}
