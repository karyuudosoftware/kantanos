var ps = panels();
for (var i = 0; i < ps.length; i++) {
    var p = ps[i];
    var names = [];
    var ws = p.widgets();
    for (var j = 0; j < ws.length; j++) names.push(ws[j].type);
    print(p.location + " height=" + p.height + " length=" + p.length + " widgets=" + names.join(","));
}
print("gridUnit=" + gridUnit);
