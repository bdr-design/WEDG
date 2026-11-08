# 3D design prototypes (web, three.js)

These are for showing the owner the look and feel before the Flutter build.
They are not the game. They run as private claude.ai artifacts.

| File | What it shows |
|---|---|
| `farm.html` | A farm in Qassim at real scale, with the herd grazing and walking, LODs, footprints and dust, labels and the glass HUD. Tap a camel to follow it. |
| `world.js` | The world for `farm.html`. Details below. |
| `camel.html` | One camel, its clips and two camera presets. |

## What `world.js` builds

- **The compound:**
  - An earth berm around it with a gate.
  - Pens in two rows with pipe rails, mesh panels and gates.
  - Concrete feeding troughs, and shades inside the pens.
- **Water and feed:**
  - An elevated water tank with a supply pipe to the troughs.
  - A feed hangar, with alfalfa bales and barley sacks outside it.
- **The owner's area:**
  - The shepherds' cabin and light poles.
  - A goat-hair tent with a Sadu rug and a fire pit.
- **Vehicles:** two pickups and a water tanker.
- **Trees:** a tamarisk windbreak and palms.
- **Roads:**
  - An asphalt road with yellow edge lines.
  - A graded track to the gate, the farm lanes, and the herd's trail.
- **The land:**
  - Patches of grass after the Wasm rain, rimth and arfaj bushes, and stones.
  - Colour changes in the sand, and dunes on the horizon.

Grass, bushes and tree foliage are crossed alpha cards with textures drawn
on canvas. Everything that repeats is instanced.

Each page loads its models as `lod0.json`, `lod1.json` and `lod2.json`. Each
file holds `{"glb": "<base64>"}` from `assets_src/camels/*.glb`, because
artifacts do not serve `.glb`. The ground is `sand.jpg`, a 1024 px copy of
the owner's Najd terrain tile.
