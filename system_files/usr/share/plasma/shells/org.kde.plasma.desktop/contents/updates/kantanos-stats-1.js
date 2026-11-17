// KantanOS update (runs once per user when the desktop starts): put KantanOS Stats in the
// top bar, just before the weather (or the system tray). KDE's own system monitor widgets
// that someone put in the top bar are left alone.
var ps = panels();
for (var i = 0; i < ps.length; i++) {
    if (ps[i].location !== "top") continue;
    var ws = ps[i].widgets();
    var have = false, anchor = null;
    for (var j = 0; j < ws.length; j++) {
        if (ws[j].type === "org.kantanos.stats") have = true;
        if (ws[j].type === "org.kantanos.weather" && !anchor) anchor = ws[j];
    }
    if (!anchor)
        for (var k = 0; k < ws.length; k++)
            if (ws[k].type === "org.kde.plasma.systemtray") anchor = ws[k];
    if (have) break;
    var at = anchor ? anchor.index : -1;
    var w = ps[i].addWidget("org.kantanos.stats");
    if (at >= 0) w.index = at;
    break;
}
