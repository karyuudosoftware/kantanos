// Plasma shell script: turn the bottom panel into the KantanOS Dock (same pinned apps),
// and move the app launcher menu to the top bar's left end.
var ps = panels();
var top = null, bottom = null;
for (var i = 0; i < ps.length; i++) {
    if (ps[i].location === "top") top = ps[i];
    if (ps[i].location === "bottom") bottom = ps[i];
}
var launchers = [];
var ws = bottom.widgets();
for (var j = 0; j < ws.length; j++) {
    var w = ws[j];
    if (w.type === "org.kde.plasma.icontasks" || w.type === "org.kantanos.dock") {
        w.currentConfigGroup = ["General"];
        launchers = w.readConfig("launchers", []);
    }
}
for (var j = 0; j < ws.length; j++) ws[j].remove();
var d = bottom.addWidget("org.kantanos.dock");
d.currentConfigGroup = ["General"];
d.writeConfig("launchers", launchers);
bottom.floating = false;
bottom.height = Math.round(gridUnit * 5.6);

var hasMenu = false;
var tws = top.widgets();
for (var j = 0; j < tws.length; j++) if (tws[j].type === "org.kde.plasma.kickoff") hasMenu = true;
if (!hasMenu) {
    var k = top.addWidget("org.kde.plasma.kickoff");
    k.currentConfigGroup = ["General"];
    k.writeConfig("icon", "kantanos");
    k.index = 0;
}
print("dock: " + launchers.length + " pinned apps, height " + bottom.height);
