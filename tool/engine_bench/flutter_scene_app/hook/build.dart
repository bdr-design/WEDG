import 'package:flutter_scene/build_hooks.dart';
import 'package:hooks/hooks.dart';

// Converts assets/terrain.glb and assets/camel_lod1.glb into flutter_scene's
// .fsceneb format at build time (written by `dart run flutter_scene:init`).
//
// compressTextures stores the 2048 px satellite image and the camel's 1K
// textures as flutter_scene's block-compressed KTX2, transcoded at load to
// what the GPU samples (ASTC, ETC2 or BC; rgba8 if none). Without it the
// importer embeds raw rgba8 (about 14 MB for the terrain image alone).
void main(List<String> args) async {
  await build(args, (input, output) async {
    buildScenes(buildInput: input, buildOutput: output, compressTextures: true);
  });
}
