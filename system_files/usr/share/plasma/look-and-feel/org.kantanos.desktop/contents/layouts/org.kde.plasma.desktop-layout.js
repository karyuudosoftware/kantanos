// KantanOS default desktop layout
// A slim top bar (menu, clock, system tray) and a floating, centred glass dock.

// ---- Top bar -------------------------------------------------------------
var topBar = new Panel;
topBar.location = "top";
topBar.height = Math.round(gridUnit * 1.5);
topBar.floating = false;
topBar.opacity = "translucent";

topBar.addWidget("org.kde.plasma.appmenu");
topBar.addWidget("org.kde.plasma.panelspacer");

var clock = topBar.addWidget("org.kde.plasma.digitalclock");
clock.currentConfigGroup = ["Appearance"];
clock.writeConfig("showDate", true);
clock.writeConfig("dateDisplayFormat", "BesideTime");
clock.writeConfig("dateFormat", "longDate");

topBar.addWidget("org.kde.plasma.panelspacer");
topBar.addWidget("org.kde.plasma.systemtray");

// ---- Dock ----------------------------------------------------------------
var dock = new Panel;
dock.location = "bottom";
dock.height = Math.round(gridUnit * 3.4);
dock.lengthMode = "fit";
dock.alignment = "center";
dock.floating = true;
dock.hiding = "dodgewindows";
dock.opacity = "translucent";

var launcher = dock.addWidget("org.kde.plasma.kickoff");
launcher.currentConfigGroup = ["General"];
launcher.writeConfig("icon", "kantanos");

var tasks = dock.addWidget("org.kde.plasma.icontasks");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", [
    "applications:org.kde.dolphin.desktop",
    "applications:org.mozilla.firefox.desktop",
    "applications:io.github.kolunmi.Bazaar.desktop",
    "applications:steam.desktop",
    "applications:org.kde.konsole.desktop",
    "applications:systemsettings.desktop"
]);
tasks.writeConfig("indicateAudioStreams", true);
tasks.writeConfig("fill", false);

dock.addWidget("org.kde.plasma.marginsseparator");
dock.addWidget("org.kde.plasma.trash");

// ---- Wallpaper -----------------------------------------------------------
var allDesktops = desktops();
for (var i = 0; i < allDesktops.length; i++) {
    var d = allDesktops[i];
    d.wallpaperPlugin = "org.kde.image";
    d.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    d.writeConfig("Image", "file:///usr/share/wallpapers/KantanOS/");
}
