// KantanOS update (runs once per user when the desktop starts): switch accounts made before
// the KantanOS Dock existed from the standard task manager to the KantanOS Dock, keeping
// their pinned apps, and put the KantanOS menu in the top bar's left corner.
// Only touches a bottom panel that still looks like the old KantanOS dock (task manager,
// no KantanOS Dock), so a dock someone rearranged in another way is left alone.
var ps = panels();
var top = null, bottom = null;
for (var i = 0; i < ps.length; i++) {
    if (ps[i].location === "top" && !top) top = ps[i];
    if (ps[i].location === "bottom" && !bottom) bottom = ps[i];
}
if (bottom) {
    var ws = bottom.widgets();
    var oldTasks = null, hasDock = false;
    for (var j = 0; j < ws.length; j++) {
        if (ws[j].type === "org.kde.plasma.icontasks") oldTasks = ws[j];
        if (ws[j].type === "org.kantanos.dock") hasDock = true;
    }
    if (oldTasks && !hasDock) {
        oldTasks.currentConfigGroup = ["General"];
        var launchers = oldTasks.readConfig("launchers", []);
        for (var j = 0; j < ws.length; j++) {
            var t = ws[j].type;
            if (t === "org.kde.plasma.icontasks" || t === "org.kde.plasma.kickoff" ||
                t === "org.kde.plasma.trash" || t === "org.kde.plasma.marginsseparator")
                ws[j].remove();
        }
        var dock = bottom.addWidget("org.kantanos.dock");
        dock.currentConfigGroup = ["General"];
        dock.writeConfig("launchers", launchers);
        bottom.floating = false;
        bottom.height = Math.round(gridUnit * 5.6);

        if (top) {
            var hasMenu = false;
            var tws = top.widgets();
            for (var j = 0; j < tws.length; j++)
                if (tws[j].type === "org.kde.plasma.kickoff") hasMenu = true;
            if (!hasMenu) {
                var menu = top.addWidget("org.kde.plasma.kickoff");
                menu.currentConfigGroup = ["General"];
                menu.writeConfig("icon", "kantanos");
                menu.index = 0;
            }
        }
    }
}
