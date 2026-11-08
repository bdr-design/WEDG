# 3D design prototypes (web, three.js)

These are for showing the owner the look and feel before the Flutter build.
They are not the game. They run as private claude.ai artifacts.

| File | What it shows |
|---|---|
| `farm.html` | A farm in Qassim at real scale, with the herd grazing and walking, LODs, footprints and dust, labels and the glass HUD. Tap a camel to follow it. |
| `camel.html` | One camel, its clips and two camera presets. |

Each page loads its models as `lod0.json`, `lod1.json` and `lod2.json`. Each
file holds `{"glb": "<base64>"}` from `assets_src/camels/*.glb`, because
artifacts do not serve `.glb`. The ground is `sand.jpg`, a 1024 px copy of
the owner's Najd terrain tile.
