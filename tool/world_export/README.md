# World export: the prototype yard into engine-neutral files

Turns the procedural three.js yard (`design/prototype3d/world.js`) into the
files in `tool/engine_bench/assets/yard/`, which any renderer can load.

**Needs:**
- Node with `npm install` in this folder, for Playwright and the glTF
  validator.
- Python 3 with numpy and Pillow.
- three.js 0.170.0 served at `/node_modules/three/`.

1. **Dump the scene.** Serve the prototype folder with `export.html` and
   `export.js` beside `world.js` (three.js on `/node_modules/three/`), then run:

   ```
   node run_export.js <port> export.json
   ```

   - `export.js` builds the yard with the prototype's own `buildWorld()`.
   - It writes, in world space:
     - every fixed mesh;
     - every scatter and tree instance;
     - the canvas textures, as PNG;
     - the vehicle placements.
   - It needs `DRAPE` and `SCATTER` exported from `world.js`, and the canvas
     textures named. `design/prototype3d/world.js` has both.
2. **Build the files.** Run:

   ```
   python3 build_yard.py export.json <out dir> <terrain.glb>
   ```

   - It merges the fixed objects into 5 materials.
   - It drapes the roads on the real terrain surface (`terrain_surface.py`).
   - It winds every ground decal to face up.
   - It writes `yard.glb`, the scatter GLBs with `yard_scatter.json`, and
     `vehicles.json` (`glbio.py` writes the GLBs).
3. **Validate.** Run `node validate.js <files>`, which uses the Khronos
   glTF validator.
4. **Compare.** Open `verify.html` next to the outputs. It loads only the
   exported files, from the prototype's drone view.
