# 3D design prototypes (web, three.js)

These are for showing the owner the look and feel before the Flutter build.
They are not the game. They run as private claude.ai artifacts.

| File | What it shows |
|---|---|
| `farm.html` | A farm in Qassim at real scale, with the herd grazing and walking, LODs, footprints and dust, labels and the glass HUD. Tap a camel to follow it. |
| `world.js` | The world for `farm.html`. Details below. |
| `terrain.js` | Builds the real terrain around the yard from `terrain/` (made by `tool/terrain3d/make_terrain.py`). |
| `camel.html` | One camel, its clips and two camera presets. |
| `models/` | The camel's three detail levels, the vehicles and the sand photo, as the page loads them (glTF in JSON). Serve them, and `terrain/`, next to `farm.html`. |

`tool/proto_app` shows this prototype inside an iPhone app (see its README).

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

## The game's rules

`engine.js` runs the game's rules engine (the packages under `packages/`,
compiled to `engine_worker.js` by `python3 tool/proto_engine/build_worker.py`;
built, not committed) in a Web Worker once the yard has loaded. The in-game
phone (`phone.js`) shows the player's own game from it: the home screen (the
date and season, the balance, the herd), الوايت and العلف, الحليب, العزبة
(building), الحراج (buying, haggling, selling and the offers on one's
listings), whose orders go to the engine, and البنك (opened by its app or by
the home's balance: the balance, today's money, every month's net with its
biggest movement, and a month opened by kind, asked of the engine with
`engine.bankMonth`). A camel bought comes on the truck
the next day and joins the yard then. The design's other phone screens come in as each works on the
engine (G3 in `docs/plan-gameplay.md`); until then they are not shown. The
frame meter (`#fps`) is one short line in the top right corner (frames a
second and the slowest 1%); a tap opens its details, with the engine's cost
to the page, and another closes them. Without the file the yard runs without
the engine.

## Weight on a phone

A performance review measured this page at a phone viewport. The fixes are
in the code, and the numbers are in
[ADR 0005](../../docs/adr/0005-3d-world.md#measured-budget-from-the-threejs-prototype-2026-11-08).
- **Ground cover:** in cells that thin out with distance.
- **Terrain:** three rings of detail.
- **Camels:** culled off screen, with one skeleton for all three detail
  levels and a lighter shadow mesh.
- **Animation:** slower updates far away.
- **Draw calls:** the yard's fixed objects are merged, and footprints are
  instanced.
- **Lighter assets:** 12k-triangle vehicles (`tool/vehicle3d/slim_vehicle.py`)
  and a 2048 px satellite image.
- **The player's SUV:** ours, built by code from the owner's photos (`tool/vehicle3d/suv_model`, made into game files by
  `ours_game.py`; the owner's choice of 11 Nov). It casts no shadow (the owner's word).
  - `veh_suvfull.json` (about 153k triangles) within 20 m or while driving, with the wheels on their own corners
    (`corner_XX` rides and steers, `wheel_XX` spins), the driver's door on its hinge (`door_FL`, with its whole window
    frame), the sill the open door shows, and the first-person eye (`eye`, `eye_look`). Each view draws only what it
    can see of it (`seat_only`, `chase_only`, `outside`).
  - `veh_suvfar.json` (about 15k) beyond 20 m.
  - `veh_suvcabin.json` (about 53k, three draws), the interior. It loads in the background a few seconds after the
    page, and is drawn only from the driver's seat or while the door stands open (the glass is dark from outside). It
    has a turning steering wheel (`steering`) and the door's trim (`doorcard_FL`), which swings with the door.
  - `car_physics.js` does the ride, the sand and the turning (suspension, grip, sinking and digging, tyre pressure,
    low range, traction and stability control, gears, hill-start assist; the turning is a single-track model with
    slip angles, so the car understeers, slides on sand and can be drifted with the stability control off). Its
    numbers are in `docs/GDD.md` section 9.1.
- **Shadows:**
  - Each camel's shadow comes from a lighter mesh.
  - The parked vehicles' shadows come from coarse copies (`veh_shas_shadow.json`, `veh_tractor_shadow.json`,
    `veh_caravan_shadow.json`: 1.4k triangles for 12k, from `tool/vehicle3d/shadow_proxy.py`), baked into the fixed
    shadow meshes and never drawn.
  - Objects smaller than 30 cm cast none.
  - The map is redrawn every other frame.

Each page loads its models as `lod0.json`, `lod1.json` and `lod2.json`. Each
file holds `{"glb": "<base64>"}` from `assets_src/camels/*.glb`, because
artifacts do not serve `.glb`. The ground is `sand.jpg`, a 1024 px copy of
the owner's Najd terrain tile.
