# 3D design prototypes (web, three.js)

These are for showing the owner the look and feel before the Flutter build.
They are not the game. They run as private claude.ai artifacts.

| File | What it shows |
|---|---|
| `farm.html` | A farm in Qassim at real scale, with the herd grazing and walking, LODs, footprints and dust, labels and the glass HUD. Tap a camel to follow it. |
| `world.js` | The world for `farm.html`. Details below. |
| `camel.html` | One camel, its clips and two camera presets. |

## What `world.js` builds

A camel yard (عزبة), not a farm.
- **The wall:** corrugated "shinko" sheets on steel posts, with a double
  gate.
- **The pens:** two rows with pipe rails, mesh panels, concrete feeding
  troughs and shades.
- **The farm room (غرفة العزبة):**
  - Block walls and a full glass front in bronze frames looking over the
    pens.
  - A carpet and floor cushions inside.
  - Split air conditioners, a roof tank, and a shaded porch with outdoor
    seating.
- **Beside the room:** a goat-hair tent with a Sadu rug and a fire pit.
- **Vehicles:** a car shade with the owner's Land Cruisers: a white LC70
  single-cab pickup (شاص) and a black LC300. A second LC70 carries alfalfa by
  the feed shed, and a water tanker stands on the lane.
- **Water, feed and staff:** an elevated water tank, an open feed shed with
  bales and sacks, and the shepherds' cabin.
- **Trees:** a few tamarisks for shade.
- **Roads:** an asphalt road, a graded track to the gate, the lanes, and the
  herd's trail.
- **The land:** grass after the Wasm rain, rimth and arfaj bushes, and
  stones.

Grass, bushes and tree foliage are crossed alpha cards with textures drawn
on canvas. Everything that repeats is instanced.

Each page loads its models as `lod0.json`, `lod1.json` and `lod2.json`. Each
file holds `{"glb": "<base64>"}` from `assets_src/camels/*.glb`, because
artifacts do not serve `.glb`. The ground is `sand.jpg`, a 1024 px copy of
the owner's Najd terrain tile.
