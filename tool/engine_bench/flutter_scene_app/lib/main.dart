// Engine benchmark for ADR 0005, flutter_scene candidate.
//
// Renders the scene in tool/engine_bench/README.md and runs its automatic
// sequence with no input: startup, then 34, 100 and 200 walking camels, each
// warmed up for 3 s and measured for 10 s. Results go to logcat (tag
// `flutter`) as `BENCH {...}` lines; `BENCH_INFO` lines add detail.
import 'dart:async';
import 'dart:developer' show Timeline;
import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/scheduler.dart';
import 'package:flutter/widgets.dart' hide Animation;
import 'package:flutter_scene/scene.dart';
import 'package:vector_math/vector_math.dart' as vm;

import 'src/bench.dart';
import 'src/platform_probe.dart';

/// Started first thing in [main]; startup_ms counts from here.
final Stopwatch _sinceMain = Stopwatch();

/// [Timeline.now] at the start of [main] (microseconds).
int _mainTimelineMicros = 0;

void main() {
  _sinceMain.start();
  _mainTimelineMicros = Timeline.now;
  WidgetsFlutterBinding.ensureInitialized();
  FlutterError.onError = (d) => _reportError('flutter', d.exception, d.stack);
  ui.PlatformDispatcher.instance.onError = (error, stack) {
    _reportError('async', error, stack);
    return true;
  };
  runApp(const BenchApp());
}

void _log(String line) {
  // The README asks for print(): it reaches logcat under the `flutter` tag in
  // release builds too.
  // ignore: avoid_print
  print(line);
}

int _errorsReported = 0;

void _reportError(String stage, Object error, StackTrace? stack) {
  if (_errorsReported++ >= 8) return;
  final where = (stack?.toString() ?? '').split('\n').take(4).join(' | ');
  _log(
    benchLine({
      'engine': kEngine,
      'stage': stage,
      'error': '$error',
      'stack': where,
    }, tag: 'BENCH_ERROR'),
  );
}

// ------------------------------------------------------------------ scene --

/// Direction toward the sun (README): a low afternoon sun in the west.
final vm.Vector3 _toSun = vm.Vector3(-0.791, 0.407, 0.457)..normalize();

/// Camera (README): from (-74, 41, 48) at (0, 1, 0), 40 degree vertical FOV.
/// The far plane covers the 70 km outer terrain ring, as in the prototype.
final PerspectiveCamera _camera = PerspectiveCamera(
  position: vm.Vector3(-74, 41, 48),
  target: vm.Vector3(0, 1, 0),
  fovRadiansY: 40 * math.pi / 180,
  fovNear: 0.5,
  fovFar: 90000,
);

/// The clear sky colour behind the scene. From this camera the view never
/// reaches the horizon, so no sky shader is drawn (see README "Sky").
const ui.Color _skyColour = ui.Color(0xFF9CC3E6);

/// Render scale cap (README): at most 1.5 physical pixels per logical pixel.
const double _maxPixelRatio = 1.5;

/// Shadow settings (README): one directional light, the engine's normal
/// filtering (rotated-Poisson PCF), a 1536 map. flutter_scene fits its
/// cascades to the view, so one cascade reaching 170 m from the camera covers
/// the herd (about 97 m away) plus about 72 m beyond it.
const int _shadowMapSize = 1536;
const int _shadowCascades = 1;
const double _shadowMaxDistance = 170;

double _srgbToLinear(int c) {
  final v = c / 255.0;
  return v <= 0.04045
      ? v / 12.92
      : math.pow((v + 0.055) / 1.055, 2.4).toDouble();
}

/// Builds the lights, sky lighting and terrain (no camels).
Future<({Node terrain, Node camel, Animation walk, Map<String, Object> info})>
_buildScene(Scene scene) async {
  final info = <String, Object>{};
  final sw = Stopwatch()..start();

  scene
    ..toneMapping = ToneMappingMode.agx
    ..exposure = 1.0;

  // Sun: the prototype's #ffdcae at 4.4, casting shadows.
  scene.directionalLight = DirectionalLight(
    direction: -_toSun,
    color: vm.Vector3(1.0, _srgbToLinear(0xdc), _srgbToLinear(0xae)),
    intensity: 4.4,
    castsShadow: true,
    shadowMapResolution: _shadowMapSize,
    shadowCascadeCount: _shadowCascades,
    shadowMaxDistance: _shadowMaxDistance,
  );

  // Image-based light baked once from a physical sky with the same sun and a
  // sand-coloured ground for the bounce. Only the lighting uses it; nothing
  // draws the sky itself (the camera never sees it).
  final sky = PhysicalSkySource(
    sunDirection: _toSun.clone(),
    turbidity: 6.5,
    mieCoefficient: 0.008,
    mieEccentricity: 0.82,
    groundColor: vm.Vector3(
      _srgbToLinear(0x9c),
      _srgbToLinear(0x71),
      _srgbToLinear(0x48),
    ),
  );
  scene
    ..skyEnvironment = SkyEnvironment(sky)
    ..environmentIntensity = 0.5;
  info['setup_ms'] = sw.elapsedMilliseconds;

  sw.reset();
  final terrain = await loadScene('assets/terrain.glb');
  info['terrain_load_ms'] = sw.elapsedMilliseconds;
  // The terrain only receives shadows, as in the prototype.
  _forEachNode(terrain, (n) => n.shadowCastingMode = ShadowCastingMode.off);
  scene.add(terrain);

  sw.reset();
  final camel = await loadScene('assets/camel_lod1.glb');
  info['camel_load_ms'] = sw.elapsedMilliseconds;
  final walk = camel.findAnimationByName('walk');
  if (walk == null) {
    throw StateError(
      'camel_lod1.glb has no "walk" clip; it has '
      '${camel.parsedAnimations.map((a) => a.name).toList()}',
    );
  }
  info['walk_clip_s'] = roundTo(walk.endTime, 3);
  return (terrain: terrain, camel: camel, walk: walk, info: info);
}

void _forEachNode(Node node, void Function(Node) visit) {
  visit(node);
  for (final child in node.children) {
    _forEachNode(child, visit);
  }
}

// -------------------------------------------------------------------- app --

class BenchApp extends StatefulWidget {
  const BenchApp({super.key});

  @override
  State<BenchApp> createState() => _BenchAppState();
}

class _BenchAppState extends State<BenchApp> {
  Scene? _scene;
  final math.Random _random = math.Random(20261108);
  final List<Node> _herd = [];

  // Flutter's frame timings (engine clock, microseconds).
  final List<FrameSample> _frames = [];

  // Timeline.now minus the engine's frame clock. Zero when they are the same
  // clock (the normal case); measured otherwise.
  int _clockOffset = 0;
  bool _clockCalibrated = false;

  // Startup: the first frame built after the scene was handed to SceneView.
  int? _readyEngineMicros;
  final Completer<FrameSample> _firstSceneFrame = Completer<FrameSample>();

  // Per-window samples from flutter_scene's own render stats.
  bool _measuring = false;
  int _lastStatsFrame = -1;
  final List<double> _engineCpuMs = [];
  final List<int> _sceneFrameStarts = [];

  @override
  void initState() {
    super.initState();
    SchedulerBinding.instance.addTimingsCallback(_onTimings);
    SchedulerBinding.instance.addPostFrameCallback((_) => _calibrateClock());
    unawaited(_run());
  }

  @override
  void dispose() {
    SchedulerBinding.instance.removeTimingsCallback(_onTimings);
    super.dispose();
  }

  int _engineNow() => Timeline.now - _clockOffset;

  void _calibrateClock() {
    if (_clockCalibrated) return;
    final frameStamp =
        SchedulerBinding.instance.currentSystemFrameTimeStamp.inMicroseconds;
    final delta = Timeline.now - frameStamp;
    // Same clock: the frame's vsync stamp is within a frame of now.
    _clockOffset = delta.abs() < 1000000 ? 0 : delta;
    _clockCalibrated = true;
  }

  void _onTimings(List<ui.FrameTiming> timings) {
    for (final t in timings) {
      final sample = FrameSample(
        buildStart: t.timestampInMicroseconds(ui.FramePhase.buildStart),
        rasterFinish: t.timestampInMicroseconds(ui.FramePhase.rasterFinish),
        totalSpan: t.totalSpan.inMicroseconds,
        build: t.buildDuration.inMicroseconds,
        raster: t.rasterDuration.inMicroseconds,
      );
      _frames.add(sample);
      final ready = _readyEngineMicros;
      if (ready != null &&
          !_firstSceneFrame.isCompleted &&
          sample.buildStart >= ready) {
        _firstSceneFrame.complete(sample);
      }
    }
    if (_frames.length > 6000) _frames.removeRange(0, _frames.length - 6000);
  }

  void _onTick(Duration elapsed, double dt) {
    final latest = _scene?.renderStats.latest;
    if (latest == null || latest.frameIndex == _lastStatsFrame) return;
    _lastStatsFrame = latest.frameIndex;
    if (_measuring) {
      _engineCpuMs.add(latest.cpuMicros / 1000);
      _sceneFrameStarts.add(latest.timestampMicros);
    }
  }

  Future<void> _run() async {
    var stage = 'init';
    try {
      await Scene.initializeStaticResources();
      final backend = gpuBackend();
      final scene = Scene();
      final view = ui.PlatformDispatcher.instance.implicitView;
      final dpr = view?.devicePixelRatio ?? 1.0;
      final pixelRatio = math.min(dpr, _maxPixelRatio);
      scene.renderScale = pixelRatio / dpr;

      stage = 'load';
      final built = await _buildScene(scene);
      _calibrateClock();

      // Hand the scene to SceneView; the next frame built is its first.
      stage = 'first_frame';
      _readyEngineMicros = _engineNow();
      final readyWallMs = _sinceMain.elapsedMilliseconds;
      setState(() => _scene = scene);
      final first = await _firstSceneFrame.future.timeout(
        const Duration(seconds: 60),
      );
      final startupMs =
          (first.rasterFinish - (_mainTimelineMicros - _clockOffset)) / 1000;
      _log(benchLine({'engine': kEngine, 'startup_ms': roundTo(startupMs, 1)}));
      _log(benchLine({'engine': kEngine, 'backend': backend}));

      final size = view?.physicalSize ?? ui.Size.zero;
      final renderView = scene.renderStats.latest?.views.firstOrNull;
      _log(
        benchLine({
          'engine': kEngine,
          'flutter_scene': '0.24.3',
          'scene_ready_ms': readyWallMs,
          ...built.info,
          'first_frame_raster_ms': roundTo(first.raster / 1000, 1),
          'clock_offset_us': _clockOffset,
          'screen_px': '${size.width.round()}x${size.height.round()}',
          'device_pixel_ratio': roundTo(dpr, 3),
          'render_pixel_ratio': roundTo(pixelRatio, 3),
          'render_px': renderView == null
              ? null
              : '${renderView.width}x${renderView.height}',
          'anti_aliasing': scene.effectiveAntiAliasingMode.name,
          'quality_tier': scene.effectiveRenderQualityTier.name,
          'tone_mapping': scene.toneMapping.name,
          'shadow':
              '${_shadowCascades}x${_shadowMapSize}px to ${_shadowMaxDistance}m, '
              'rotatedPoisson PCF, camels only cast',
          'ibl': 'PhysicalSkySource baked once (SkyEnvironment)',
          'textures': 'compressTextures (universal-block KTX2, transcoded)',
        }, tag: 'BENCH_INFO'),
      );

      for (final n in kHerdSizes) {
        stage = 'herd_$n';
        await _measureHerd(scene, n, built.camel, built.walk);
      }
    } on Object catch (error, stack) {
      _reportError(stage, error, stack);
    } finally {
      _log('BENCH_DONE');
    }
  }

  Future<void> _measureHerd(
    Scene scene,
    int n,
    Node template,
    Animation walk,
  ) async {
    // Spawn N camels on a fresh jittered grid.
    final spawn = Stopwatch()..start();
    for (final node in _herd) {
      scene.remove(node);
    }
    _herd.clear();
    final up = vm.Vector3(0, 1, 0);
    for (final slot in herdLayout(
      n,
      random: _random,
      clipLength: walk.endTime,
    )) {
      final camel = template.clone()
        ..localTransform = vm.Matrix4.compose(
          vm.Vector3(slot.x, 0, slot.z),
          vm.Quaternion.axisAngle(up, slot.heading),
          vm.Vector3.all(1),
        );
      camel.createAnimationClip(camel.findAnimationByName('walk') ?? walk)
        ..loop = true
        ..weight = 1
        ..gotoAndPlay(slot.clipOffset);
      scene.add(camel);
      _herd.add(camel);
    }
    final spawnMs = spawn.elapsedMilliseconds;

    // Warm up 3 s, then measure 10 s.
    await Future<void>.delayed(const Duration(seconds: 3));
    final pacedStart = scene.pacedFrameCount;
    final sceneFramesStart = scene.renderStats.frameCount;
    _engineCpuMs.clear();
    _sceneFrameStarts.clear();
    final windowWall = Stopwatch()..start();
    final windowStart = _engineNow();
    _measuring = true;
    await Future<void>.delayed(const Duration(seconds: 10));
    final windowEnd = _engineNow();
    _measuring = false;
    final seconds = windowWall.elapsedMicroseconds / 1e6;
    final sceneFrames = scene.renderStats.frameCount - sceneFramesStart;
    final paced = scene.pacedFrameCount - pacedStart;
    final rssBytes = currentRssBytes();
    final stats = scene.renderStats.latest;

    // Release builds deliver frame timings about once a second: wait for the
    // batch holding the window's last frames.
    final flush = Stopwatch()..start();
    while (flush.elapsedMilliseconds < 3000 &&
        !_frames.any((f) => f.buildStart >= windowEnd)) {
      await Future<void>.delayed(const Duration(milliseconds: 100));
    }

    final window = framesInWindow(_frames, windowStart, windowEnd);
    final total = percentiles(window.map((f) => f.totalSpan / 1000));
    final engine = percentiles(_engineCpuMs);
    final intervals = <double>[
      for (var i = 1; i < _sceneFrameStarts.length; i++)
        (_sceneFrameStarts[i] - _sceneFrameStarts[i - 1]) / 1000,
    ];
    final sceneInterval = percentiles(intervals);
    _log(
      benchLine({
        'engine': kEngine,
        'n': n,
        'frames': window.length,
        'fps': roundTo(window.length / seconds, 1),
        'p50_ms': roundTo(total.p50),
        'p90_ms': roundTo(total.p90),
        'p99_ms': roundTo(total.p99),
        'rss_mb': rssBytes == null ? null : roundTo(rssBytes / 1048576, 1),
        'engine_p50_ms': roundTo(engine.p50),
        // flutter_scene re-presents its previous image instead of encoding a
        // new one while the GPU is a frame behind (maxGpuFramesInFlight = 1),
        // so Flutter frames can outnumber new scene images.
        'scene_frames': sceneFrames,
        'scene_fps': roundTo(sceneFrames / seconds, 1),
        'paced_frames': paced,
      }),
    );
    final passes = <String, Object>{
      for (final view in stats?.views ?? const <RenderViewStats>[])
        for (final pass in view.passes)
          pass.name: {
            'draws': pass.counters.draws,
            'tris': pass.counters.vertices ~/ 3,
            'cpu_ms': roundTo(pass.cpuMicros / 1000),
          },
    };
    _log(
      benchLine({
        'engine': kEngine,
        'n': n,
        'spawn_ms': spawnMs,
        'window_s': roundTo(seconds, 2),
        'build_p50_ms': roundTo(
          percentiles(window.map((f) => f.build / 1000)).p50,
        ),
        'raster_p50_ms': roundTo(
          percentiles(window.map((f) => f.raster / 1000)).p50,
        ),
        'engine_p90_ms': roundTo(engine.p90),
        'scene_interval_p50_ms': roundTo(sceneInterval.p50),
        'scene_interval_p90_ms': roundTo(sceneInterval.p90),
        'scene_interval_p99_ms': roundTo(sceneInterval.p99),
        'draws': stats?.counters.draws,
        'tris': stats == null ? null : stats.counters.vertices ~/ 3,
        'instances': stats?.counters.instances,
        'pipeline_builds': stats?.counters.pipelineBuilds,
        'passes': passes,
      }, tag: 'BENCH_INFO'),
    );
  }

  @override
  Widget build(BuildContext context) {
    final scene = _scene;
    // No MaterialApp: the bench draws nothing but the scene.
    return Directionality(
      textDirection: TextDirection.ltr,
      child: ColoredBox(
        color: _skyColour,
        child: scene == null
            ? const SizedBox.expand()
            : SceneView(scene, camera: _camera, onTick: _onTick),
      ),
    );
  }
}
