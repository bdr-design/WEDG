import 'dart:developer' show Timeline;
import 'dart:ui' show FramePhase, FrameTiming;

import 'package:flutter/scheduler.dart';

import 'bench_stats.dart';

/// Collects Flutter's [FrameTiming]s and Thermion's own render times.
///
/// Every timestamp is on the clock of `Timeline.now` (µs), which is also the
/// clock of [FrameTiming] timestamps, so frames are assigned to a measuring
/// window by when they started, not by when the engine reported them (Flutter
/// reports timings in batches, up to about a second late in release builds).
class FrameRecorder {
  final List<TimedSample> _flutterFrames = [];
  final List<TimedSample> _engineFrames = [];
  bool _listening = false;

  void start() {
    if (_listening) return;
    _listening = true;
    SchedulerBinding.instance.addTimingsCallback(_onTimings);
  }

  void _onTimings(List<FrameTiming> timings) {
    for (final t in timings) {
      _flutterFrames.add(
        TimedSample(
          t.timestampInMicroseconds(FramePhase.vsyncStart),
          t.totalSpan.inMicroseconds,
        ),
      );
    }
  }

  /// Called once per Thermion render with its start time and duration.
  void addEngineFrame(int startUs, int durationUs) =>
      _engineFrames.add(TimedSample(startUs, durationUs));

  /// Number of Thermion renders so far.
  int get engineFrameCount => _engineFrames.length;

  /// Flutter `totalSpan`s (ms) of frames that began in [fromUs, toUs).
  List<double> flutterFrameMs(int fromUs, int toUs) =>
      durationsInWindow(_flutterFrames, fromUs, toUs);

  /// Thermion render times (ms) of renders that began in [fromUs, toUs).
  List<double> engineFrameMs(int fromUs, int toUs) =>
      durationsInWindow(_engineFrames, fromUs, toUs);

  /// Drops samples older than [beforeUs] so memory stays flat.
  void discardBefore(int beforeUs) {
    _flutterFrames.removeWhere((s) => s.startUs < beforeUs);
    _engineFrames.removeWhere((s) => s.startUs < beforeUs);
  }

  static int nowUs() => Timeline.now;
}
