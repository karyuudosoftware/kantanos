// KantanOS update (runs once per user when the desktop starts): put KantanOS Weather in the
// top bar. It replaces KDE's weather widget where someone added that (KDE's widget only
// knows the towns of a few weather services, so many towns can't be found), keeping its
// place in the bar; otherwise it goes just before the system tray.
var ps = panels();
for (var i = 0; i < ps.length; i++) {
    if (ps[i].location !== "top") continue;
    var ws = ps[i].widgets();
    var have = false, old = null, tray = null;
    for (var j = 0; j < ws.length; j++) {
        if (ws[j].type === "org.kantanos.weather") have = true;
        if (ws[j].type === "org.kde.plasma.weather" && !old) old = ws[j];
        if (ws[j].type === "org.kde.plasma.systemtray") tray = ws[j];
    }
    if (have) break;
    var at = old ? old.index : (tray ? tray.index : -1);
    if (old) old.remove();
    var w = ps[i].addWidget("org.kantanos.weather");
    if (at >= 0) w.index = at;
    break;
}
