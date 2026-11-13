#!/usr/bin/env python3
"""Generates the Explorer-style toolbar layout for the file manager (Dolphin).

Input : tools/dolphin/dolphinui-upstream.rc  (Dolphin's own definition, from its source)
Output: system_files/etc/skel/.local/share/kxmlgui5/dolphin/dolphinui.rc

Two rows, like Windows 11 Explorer:
  navigation row : Back  Forward  Up  Refresh  [ address bar ]  Search  Menu
  command row    : New  |  Cut  Copy  Paste  Rename  Delete  |  Sort  View

The version number is raised far above upstream's so a Dolphin update does not silently
throw the layout away. When upstream's file changes, refresh the reference copy and rerun.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
src = (ROOT / "tools/dolphin/dolphinui-upstream.rc").read_text(encoding="utf-8")

upstream_version = int(re.search(r'<gui name="dolphin" version="(\d+)"', src).group(1))
src = src.replace(f'version="{upstream_version}"', f'version="{upstream_version + 1000}"', 1)

NAV = ["go_back", "go_forward", "go_up", "view_redisplay", "url_navigators", "toggle_search", "hamburger_menu"]
COMMANDS = ["new_menu", None, "edit_cut", "edit_copy", "edit_paste", "renamefile", "movetotrash", None, "sort", "view_mode"]
# Short, Explorer-style button labels.
LABELS = {"new_menu": "New", "movetotrash": "Delete", "sort": "Sort", "view_mode": "View"}
# Upstream hides the text of these; the command row shows text beside every icon.
SHOW_TEXT = ["edit_cut", "edit_copy", "edit_paste", "view_mode"]
# Icon only (no text) on the navigation row.
ICON_ONLY = ["view_redisplay"]


def items(names):
    pad = " " * 8
    return "".join(pad + ("<Separator />" if n is None else f'<Action name="{n}" />') + "\n" for n in names)


toolbars = (
    '<ToolBar noMerge="1" name="mainToolBar" >\n'
    '        <text context="@title:menu">Navigation</text>\n'
    + items(NAV)
    + "    </ToolBar>\n"
    '    <ToolBar noMerge="1" name="commandToolBar" newline="true" iconText="textbesideicon" >\n'
    '        <text context="@title:menu">Commands</text>\n'
    + items(COMMANDS)
    + "    </ToolBar>"
)

out, n = re.subn(r'<ToolBar noMerge="1" name="mainToolBar" >.*?</ToolBar>', lambda m: toolbars, src, flags=re.S)
assert n == 1, "upstream toolbar block not found - the reference file changed shape"

for name in SHOW_TEXT:
    out = re.sub(rf'\s*<Action priority="0" name="{name}"\s*/>', "", out)

MARK = '<ActionProperties scheme="Default">'
assert out.count(MARK) == 1, "ActionProperties block not found"
props = "".join(f'\n        <Action name="{k}" iconText="{v}"/>' for k, v in LABELS.items())
props += "".join(f'\n        <Action priority="0" name="{k}"/>' for k in ICON_ONLY)
out = out.replace(MARK, MARK + props)

dst = ROOT / "system_files/etc/skel/.local/share/kxmlgui5/dolphin/dolphinui.rc"
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_text(out, encoding="utf-8", newline="\n")
print(f"wrote {dst.relative_to(ROOT)} (upstream version {upstream_version})")
