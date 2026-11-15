// Test helper: put the VM user's panels back to the old (pre-KantanOS-Dock) layout.
var ps = panels();
for (var i = 0; i < ps.length; i++) {
    var p = ps[i];
    var ws = p.widgets();
    if (p.location === "top") {
        for (var j = 0; j < ws.length; j++) if (ws[j].type === "org.kde.plasma.kickoff") ws[j].remove();
    }
    if (p.location === "bottom") {
        for (var j = 0; j < ws.length; j++) ws[j].remove();
        var k = p.addWidget("org.kde.plasma.kickoff");
        k.currentConfigGroup = ["General"]; k.writeConfig("icon", "kantanos");
        var t = p.addWidget("org.kde.plasma.icontasks");
        t.currentConfigGroup = ["General"];
        t.writeConfig("launchers", ["applications:org.kde.dolphin.desktop", "applications:org.kde.konsole.desktop", "applications:systemsettings.desktop"]);
        p.addWidget("org.kde.plasma.marginsseparator");
        p.addWidget("org.kde.plasma.trash");
        p.height = Math.round(gridUnit * 3.4);
        p.floating = true;
    }
}
print("old layout restored");
