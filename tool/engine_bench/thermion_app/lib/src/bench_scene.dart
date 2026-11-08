import 'dart:async';

// The SH-only indirect light (no KTX environment) is built through the FFI
// classes; the public ThermionViewer API only loads IBLs from KTX files.
// ignore: implementation_imports
import 'package:thermion_dart/src/filament/src/implementation/ffi_filament_app.dart';
// ignore: implementation_imports
import 'package:thermion_dart/src/filament/src/implementation/ffi_indirect_light.dart';
import 'package:thermion_flutter/thermion_flutter.dart';

import 'herd_layout.dart';
import 'sky_light.dart';

/// The fixed benchmark scene of tool/engine_bench/README.md, built with
/// Thermion (Filament). Camels are added by [spawnCamels].
class BenchScene {
  BenchScene(this.viewer);

  final ThermionViewer viewer;

  static const String terrainAsset = 'assets/terrain.glb';
  static const String camelAsset = 'assets/camel_lod1.glb';

  /// Direction toward the sun (README): a low afternoon sun in the west.
  static final Vector3 towardSun = Vector3(-0.791, 0.407, 0.457);
  static final Vector3 cameraPosition = Vector3(-74, 41, 48);
  static final Vector3 cameraTarget = Vector3(0, 1, 0);
  static const double verticalFovDegrees = 40;
  static const double near = 0.5;

  /// The far ring of the terrain reaches about 50 km. Filament uses `far`
  /// for culling; its depth buffer is reversed-Z, so a 0.5 m near plane
  /// keeps enough precision.
  static const double far = 60000;

  /// Filament shadow maps must be a power of two, so 1536 is not possible.
  /// 2048 is used: never coarser than the README's 1536 (1024 would be).
  static const int shadowMapSize = 2048;

  /// The camera is ~97 m from the herd; clipping shadows at 170 m from the
  /// camera makes the single shadow map cover about ±72 m around the herd.
  static const double shadowFar = 170;

  /// Sun illuminance (lux) and IBL luminance, matched to Filament's default
  /// exposure (f/16, 1/125 s, ISO 100: "sunny 16").
  static const double sunLux = 100000;
  static const double skyIntensity = 30000;

  ThermionAsset<dynamic>? _terrain;
  ThermionAsset<dynamic>? _camelSource;
  final List<ThermionAsset<dynamic>> _camels = [];
  int _walkIndex = -1;
  double _walkDuration = 1.5;

  int get camelCount => _camels.length;

  FFIFilamentApp get _app => viewer.app as FFIFilamentApp;

  /// Sets up everything except the camels.
  Future<void> build({required double aspect}) async {
    final view = viewer.view;

    // Thermion's usual setup (as in its ViewerWidget): post-processing on
    // (ACES tone mapping, dithering) with FXAA, no MSAA, no TAA.
    await viewer.setPostProcessing(true);
    await viewer.setAntiAliasing(false, true, false);

    // Shadows: one directional light, PCF (Filament's default filter).
    await view.setShadowsEnabled(true);
    await view.setShadowType(ShadowType.PCF);

    // Sky: a constant clear-sky colour behind everything...
    final scene = await view.getScene();
    final skybox = await _app.createColoredSkybox(
      r: kSkyColour.r,
      g: kSkyColour.g,
      b: kSkyColour.b,
      a: 1,
      showSun: true,
    );
    await scene.setSkybox(skybox);

    // ...and ambient image-based light from the same sky (irradiance
    // spherical harmonics only: no reflection cubemap, no KTX file needed).
    final ibl = await FFIIndirectLight.fromIrradianceHarmonics(
      _app,
      hemisphereHarmonics(kSkyRadiance, kGroundRadiance),
      intensity: skyIntensity,
    );
    await scene.setIndirectLight(ibl);

    // Sun. Filament wants the direction the light travels, i.e. away from
    // the sun.
    final sun = await viewer.addDirectLight(
      DirectLight(
        type: LightType.SUN,
        colorTemperature: 5200,
        intensity: sunLux,
        castShadows: true,
        direction: -towardSun.normalized(),
        position: Vector3.zero(),
      ),
    );
    await _app.lightManager.setShadowOptions(
      sun,
      ShadowOptions(
        mapSize: shadowMapSize,
        shadowCascades: 1,
        shadowFar: shadowFar,
        shadowFarHint: shadowFar,
      ),
    );

    await setCamera(aspect);

    // Terrain: receives shadows, casts none (only camels cast live shadows,
    // as ADR 0005 plans; the yard is flat).
    final terrain = await viewer.loadGltf(terrainAsset);
    await terrain.setCastShadows(false);
    await terrain.setReceiveShadows(true);
    _terrain = terrain;
  }

  /// Points the camera as the README says; called again once the real
  /// viewport size is known.
  Future<void> setCamera(double aspect) async {
    final camera = await viewer.getActiveCamera();
    await camera.setProjectionFromVerticalFieldOfView(
      verticalFovDegrees,
      near,
      far,
      aspect,
    );
    await camera.lookAt(cameraPosition, focus: cameraTarget);
  }

  bool get hasTerrain => _terrain != null;

  /// Grows the herd to [n] camels (it never shrinks) and lays all of them
  /// out on the jittered grid for [n].
  ///
  /// Uses glTF instancing (gltfio `FilamentInstance`s): every camel shares
  /// one vertex/index buffer, one set of textures and one material instance
  /// with the source asset, but has its own entities, skin and animator.
  /// Filament draws each skinned instance as its own draw call; its
  /// automatic instancing skips skinned renderables.
  ///
  /// Nothing here runs per frame: transforms are static and the walk cycle
  /// is advanced natively by Thermion's AnimationManager on its render
  /// thread, so a frame costs one Dart→native render call whatever N is.
  Future<void> spawnCamels(int n) async {
    final fresh = <ThermionAsset<dynamic>>[];
    var source = _camelSource;
    if (source == null) {
      // Pre-allocating the first batch at load time is the documented fast
      // path; later growth uses createInstance().
      source = await viewer.loadGltf(
        camelAsset,
        addToScene: false,
        initialInstances: n,
      );
      _camelSource = source;
      final names = await source.getGltfAnimationNames();
      _walkIndex = names.indexOf('walk');
      if (_walkIndex < 0) {
        throw StateError('camel has no "walk" clip, only $names');
      }
      _walkDuration = await source.getGltfAnimationDuration(_walkIndex);
      fresh.addAll(await source.getInstances());
    }
    while (_camels.length + fresh.length < n) {
      fresh.add(await source.createInstance());
    }

    final layout = herdLayout(n, clipDuration: _walkDuration);
    final all = [..._camels, ...fresh];
    for (var i = 0; i < all.length; i++) {
      final p = layout[i];
      await all[i].setTransform(
        Matrix4.compose(
          Vector3(p.x, 0, p.z), // the yard is flat at y = 0
          Quaternion.axisAngle(Vector3(0, 1, 0), p.heading),
          Vector3.all(1),
        ),
      );
    }
    for (var i = _camels.length; i < all.length; i++) {
      final camel = all[i];
      await camel.setCastShadows(true);
      await camel.setReceiveShadows(true);
      await viewer.addToScene(camel);
      await camel.playGltfAnimation(
        _walkIndex,
        loop: true,
        startOffset: layout[i].clipOffset,
      );
    }
    _camels
      ..clear()
      ..addAll(all);
  }

  /// Aspect ratio of the current viewport, or null before it is known.
  Future<double?> viewportAspect() async {
    final vp = await viewer.view.getViewport();
    if (vp.width <= 0 || vp.height <= 0) return null;
    return vp.width / vp.height;
  }

  /// Renderables Filament drew in the last frame, after culling.
  int visibleRenderables() => viewer.view.getVisibleRenderableCount();
}
