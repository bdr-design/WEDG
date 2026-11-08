# 3D design prototypes (web, three.js)

These are for showing the owner the look and feel before the Flutter build.
They are not the game. They run as private claude.ai artifacts.

| File | What it shows |
|---|---|
| `farm.html` | A farm in Qassim at real scale, with the herd grazing and walking, LODs, footprints and dust, labels and the glass HUD. Tap a camel to follow it. |
| `world.js` | The world for `farm.html`. Details below. |
| `terrain.js` | Builds the real terrain around the yard from `terrain/` (made by `tool/terrain3d/make_terrain.py`). |
| `camel.html` | One camel, its clips and two camera presets. |

## Where the yard is

The yard stands on a real plain in western Qassim (25.8148 N, 42.9015 E,
765 m).
- **Aban al-Asmar** (1225 m) is 6.4 km to the east, and **Aban al-Ahmar**
  (1309 m) is 37 km to the south-west.
- **Wadi al-Rumah** runs between them, with Nafud sand to the west.
- **Data:** the 70 × 66 km terrain uses 30 m elevation (AWS Terrain Tiles)
  and a cloud-free Sentinel-2 scene from 2026-01-17 (NASA HLS). The owner's
  sand photo is blended in close to the camera.

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
- **Beside the room:** a goat-hair tent.
  - Wooden poles, carpets, and floor cushions and rolls along the walls.
  - A Sadu curtain (القاطع), and a hearth with glowing embers.
  - Three brass dallahs, a thermos, a tray of cups, dates and a lantern.
  - A Sadu rug and a fire pit outside.
- **Vehicles:** a car shade with the owner's Land Cruisers: a white LC70
  single-cab pickup (شاص) and a black LC300. A second LC70 carries alfalfa by
  the feed shed, and a water tanker stands on the lane.
- **Water, feed and staff:** an elevated water tank, an open feed shed with
  bales and sacks, and the shepherds' cabin.
- **The grazing ground (مسراح):** about 330 m out along a track.
  - The shepherd's caravan on a flatbed trailer, coupled to its tractor unit.
  - A portable trough, bales, and the herd grazing.
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
