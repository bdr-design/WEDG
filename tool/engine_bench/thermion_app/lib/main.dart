import 'dart:async';
import 'dart:io' show ProcessInfo;
import 'dart:math' as math;
import 'dart:ui' as ui;

import 'package:flutter/scheduler.dart';
import 'package:flutter/widgets.dart';
import 'package:logging/logging.dart';
import 'package:thermion_flutter/thermion_flutter.dart'
    show FilamentApp, ThermionFlutterPlugin, ThermionViewer, ThermionWidget;
// Thermion drives its render loop from a native vsync source through this
// scheduler. The benchmark swaps in a handler that times each render.
// ignore: implementation_imports
import 'package:thermion_flutter/src/platform/src/frame_scheduler.dart';

import 'src/bench_scene.dart';
import 'src/bench_stats.dart';
import 'src/frame_recorder.dart';

const String kEngine = 'thermion';
const List<int> kHerdSizes = [34, 100, 200];
const Duration kWarmUp = Duration(seconds: 3);
const Duration kMeasure = Duration(seconds: 10);

/// Flutter reports frame timings in batches; wait this long after a window
/// so its last frames have arrived before computing the numbers.
const Duration kTimingFlush = Duration(milliseconds: 1500);

/// README render scale: at most 1.5 rendered pixels per logical pixel (the
/// three.js prototype's setPixelRatio(min(devicePixelRatio, 1.5))).
const double kMaxRenderScale = 1.5;

void main() {
  final mainStartUs = FrameRecorder.nowUs();
  WidgetsFlutterBinding.ensureInitialized();
  final recorder = FrameRecorder()..start();
  // Thermion logs through package:logging; only surface real errors (its
  // per-frame JANK warnings would flood logcat under SwiftShader).
  Logger.root.onRecord.listen((r) {
    if (r.level >= Level.SEVERE) {
      print('thermion ${r.level.name} ${r.loggerName}: ${r.message}');
    }
  });
  runApp(BenchApp(mainStartUs: mainStartUs, recorder: recorder));
}

class BenchApp extends StatefulWidget {
  const BenchApp({
    super.key,
    required this.mainStartUs,
    required this.recorder,
  });

  final int mainStartUs;
  final FrameRecorder recorder;

  @override
  State<BenchApp> createState() => _BenchAppState();
}

class _BenchAppState extends State<BenchApp> {
  ThermionViewer? _viewer;
  String _status = 'starting';

  FrameRecorder get _recorder => widget.recorder;

  @override
  void initState() {
    super.initState();
    unawaited(_runGuarded());
  }

  void _setStatus(String status) {
    if (mounted) setState(() => _status = status);
  }

  Future<void> _runGuarded() async {
    try {
      await _run();
    } catch (error, stack) {
      print(benchLine({'engine': kEngine, 'error': '$error'}));
      print('$stack');
    } finally {
      print('BENCH_DONE');
      _setStatus('done');
    }
  }

  Future<void> _run() async {
    // 1. Engine, view and the native render loop.
    final viewer = await ThermionFlutterPlugin.createViewer().timeout(
      const Duration(seconds: 60),
    );
    _installTimedRenderLoop();
    setState(() => _viewer = viewer);

    // 2. The scene without camels.
    final scene = BenchScene(viewer);
    await scene
        .build(aspect: _windowAspect())
        .timeout(const Duration(seconds: 90));

    // 3. First frame showing it: the texture is bound to a swap chain,
    // Filament has rendered the scene, the GPU has finished, and Flutter has
    // composited it.
    await _waitForFirstSceneFrame(viewer).timeout(const Duration(seconds: 60));
    final startupMs = (FrameRecorder.nowUs() - widget.mainStartUs) / 1000;
    print(benchLine({'engine': kEngine, 'startup_ms': startupMs.round()}));

    // The ThermionWidget re-derives the projection from the texture size;
    // set the README's 40° vertical field of view on the real aspect.
    final aspect = await scene.viewportAspect();
    if (aspect != null) await scene.setCamera(aspect);

    // 4. The herd sizes.
    for (final n in kHerdSizes) {
      _setStatus('spawning $n');
      final spawnStartUs = FrameRecorder.nowUs();
      await scene.spawnCamels(n).timeout(const Duration(seconds: 60));
      final spawnMs = (FrameRecorder.nowUs() - spawnStartUs) / 1000;
      _setStatus('$n camels');
      await Future<void>.delayed(kWarmUp);

      final fromUs = FrameRecorder.nowUs();
      await Future<void>.delayed(kMeasure);
      final toUs = FrameRecorder.nowUs();
      final rssMb = ProcessInfo.currentRss / (1024 * 1024);
      final visible = scene.visibleRenderables();
      final viewport = await viewer.view.getViewport();
      await Future<void>.delayed(kTimingFlush);

      print(
        measurementLine(
          engine: kEngine,
          n: n,
          frameMs: _recorder.flutterFrameMs(fromUs, toUs),
          engineMs: _recorder.engineFrameMs(fromUs, toUs),
          windowSeconds: (toUs - fromUs) / 1e6,
          rssMb: rssMb,
          extra: {
            'spawn_ms': spawnMs.round(),
            'visible_renderables': visible,
            'render_px': '${viewport.width}x${viewport.height}',
          },
        ),
      );
      _recorder.discardBefore(toUs);
    }
  }

  /// Replaces Thermion's frame handler with one that does the same work
  /// (`FilamentApp.render`, which runs the request-frame hooks, advances
  /// the animations and renders every attached view on Thermion's render
  /// thread) and records how long it took. The scheduler still drops ticks
  /// while a render is in flight, exactly as before.
  ///
  /// The stock handler also notifies the texture registry after each frame;
  /// on Android that only acknowledges the frame (a no-op) and retires
  /// textures replaced by a resize, which never happens here.
  void _installTimedRenderLoop() {
    FrameScheduler.instance.setFrameHandler((int frameTimeNanos) async {
      final app = FilamentApp.instance;
      if (app == null) return;
      final startUs = FrameRecorder.nowUs();
      await app.render(frameTimeInNanos: frameTimeNanos);
      _recorder.addEngineFrame(startUs, FrameRecorder.nowUs() - startUs);
    });
  }

  Future<void> _waitForFirstSceneFrame(ThermionViewer viewer) async {
    final app = viewer.app;
    while (app.renderManager.getAttachedSwapChains(viewer.view).isEmpty) {
      await Future<void>.delayed(const Duration(milliseconds: 4));
    }
    // A render that started after the swap chain was attached has finished.
    final target = _recorder.engineFrameCount + 2;
    while (_recorder.engineFrameCount < target) {
      await Future<void>.delayed(const Duration(milliseconds: 2));
    }
    // Wait for the GPU to execute it (Filament's driver thread is async).
    await app.flush();
    // And for Flutter to composite the new texture contents.
    SchedulerBinding.instance.scheduleFrame();
    await SchedulerBinding.instance.endOfFrame;
  }

  double _windowAspect() {
    final views = ui.PlatformDispatcher.instance.views;
    if (views.isEmpty) return 0.5;
    final size = views.first.physicalSize;
    if (size.width <= 0 || size.height <= 0) return 0.5;
    return size.width / size.height;
  }

  @override
  Widget build(BuildContext context) {
    final viewer = _viewer;
    return Directionality(
      textDirection: TextDirection.ltr,
      child: ColoredBox(
        color: const Color(0xFF8AB8EB),
        child: Stack(
          fit: StackFit.expand,
          children: [
            if (viewer != null)
              _CappedPixelRatio(
                maxRatio: kMaxRenderScale,
                child: ThermionWidget(viewer: viewer),
              ),
            Positioned(
              left: 12,
              bottom: 12,
              child: Text(
                'Bench Thermion · $_status',
                style: const TextStyle(color: Color(0xFFFFFFFF), fontSize: 12),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Caps the device pixel ratio seen by [child]. ThermionWidget sizes its
/// render texture as logical size × devicePixelRatio, so this is Thermion's
/// render scale; Flutter stretches the texture to the screen.
class _CappedPixelRatio extends StatelessWidget {
  const _CappedPixelRatio({required this.maxRatio, required this.child});

  final double maxRatio;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final mq = MediaQuery.maybeOf(context);
    if (mq == null) return child;
    return MediaQuery(
      data: mq.copyWith(
        devicePixelRatio: math.min(mq.devicePixelRatio, maxRatio),
      ),
      child: child,
    );
  }
}
