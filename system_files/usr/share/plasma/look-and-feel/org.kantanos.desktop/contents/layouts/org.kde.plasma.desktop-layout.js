// KantanOS default desktop layout
// A slim top bar (KantanOS menu, app menu, clock, system tray) and the KantanOS Dock: a
// glass bar of apps that magnify under the pointer, like the macOS dock.

// ---- Top bar -------------------------------------------------------------
var topBar = new Panel;
topBar.location = "top";
topBar.height = Math.round(gridUnit * 1.5);
topBar.floating = false;
topBar.opacity = "translucent";

// The KantanOS menu sits in the top-left corner; the dock's 簡単 button opens it too.
var menu = topBar.addWidget("org.kde.plasma.kickoff");
menu.currentConfigGroup = ["General"];
menu.writeConfig("icon", "kantanos");

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
// The panel is tall and see-through (the Kantan Glass theme leaves bottom panels empty);
// the dock widget draws its glass bar along the bottom and magnifies icons into the space
// above it.
var dock = new Panel;
dock.location = "bottom";
dock.height = Math.round(gridUnit * 5.6);
dock.lengthMode = "fit";
dock.alignment = "center";
dock.floating = false;
dock.hiding = "dodgewindows";

var tasks = dock.addWidget("org.kantanos.dock");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", [
    "applications:kantanos-modes.desktop",
    "applications:org.kde.dolphin.desktop",
    "applications:org.mozilla.firefox.desktop",
    "applications:io.github.kolunmi.Bazaar.desktop",
    "applications:steam.desktop",
    "applications:org.kde.konsole.desktop",
    "applications:systemsettings.desktop"
]);

// ---- Wallpaper -----------------------------------------------------------
var allDesktops = desktops();
for (var i = 0; i < allDesktops.length; i++) {
    var d = allDesktops[i];
    d.wallpaperPlugin = "org.kde.image";
    d.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
    d.writeConfig("Image", "file:///usr/share/wallpapers/KantanOS/");
}
