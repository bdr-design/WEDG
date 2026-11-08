// Pure-Dart parts of the benchmark: the herd layout, frame-time statistics
// and the BENCH line format. No Flutter or GPU imports, so they are unit
// tested on the host (test/bench_test.dart).
import 'dart:convert';
import 'dart:math' as math;

/// The engine name every BENCH line carries.
const String kEngine = 'flutter_scene';

/// Herd sizes, in the order the README runs them.
const List<int> kHerdSizes = [34, 100, 200];

/// Grid spacing between camels, in metres (README).
const double kHerdSpacing = 4.0;

/// Each camel is moved by up to this much along x and z from its grid point.
/// The README asks for a "jittered grid" without an amplitude; 0.6 m keeps a
/// 2.8 m camel clear of its neighbours at any heading.
const double kHerdJitter = 0.6;

/// One camel's place in the herd.
class HerdSlot {
  const HerdSlot(this.x, this.z, this.heading, this.clipOffset);

  /// Position on the ground (y = 0 is the flat yard), metres.
  final double x;
  final double z;

  /// Rotation about +y, radians.
  final double heading;

  /// Start time inside the walk clip, seconds.
  final double clipOffset;
}

/// [n] camels on a jittered square grid with [spacing] metres between grid
/// points, centred on the origin. Each camel gets a random heading and its own
/// offset into a clip [clipLength] seconds long.
List<HerdSlot> herdLayout(
  int n, {
  required math.Random random,
  required double clipLength,
  double spacing = kHerdSpacing,
  double jitter = kHerdJitter,
}) {
  if (n <= 0) return const [];
  final cols = math.sqrt(n).ceil();
  final rows = (n / cols).ceil();
  final slots = <HerdSlot>[];
  for (var i = 0; i < n; i++) {
    final row = i ~/ cols;
    final col = i % cols;
    final x =
        (col - (cols - 1) / 2) * spacing + (random.nextDouble() * 2 - 1) * jitter;
    final z =
        (row - (rows - 1) / 2) * spacing + (random.nextDouble() * 2 - 1) * jitter;
    slots.add(
      HerdSlot(
        x,
        z,
        random.nextDouble() * 2 * math.pi,
        random.nextDouble() * clipLength,
      ),
    );
  }
  return slots;
}

/// Nearest-rank percentile of an ascending [sorted] list, [q] in 0..1.
double percentile(List<double> sorted, double q) {
  if (sorted.isEmpty) return double.nan;
  final rank = (q * sorted.length).ceil().clamp(1, sorted.length);
  return sorted[rank - 1];
}

/// p50/p90/p99 of [values] (unsorted), in their own unit.
({double p50, double p90, double p99}) percentiles(Iterable<double> values) {
  final sorted = values.toList()..sort();
  return (
    p50: percentile(sorted, 0.50),
    p90: percentile(sorted, 0.90),
    p99: percentile(sorted, 0.99),
  );
}

/// A finished frame as Flutter reported it (FrameTiming), in microseconds of
/// the engine clock.
class FrameSample {
  const FrameSample({
    required this.buildStart,
    required this.rasterFinish,
    required this.totalSpan,
    required this.build,
    required this.raster,
  });

  final int buildStart;
  final int rasterFinish;

  /// FrameTiming.totalSpan (vsync start to raster finish).
  final int totalSpan;
  final int build;
  final int raster;
}

/// The frames whose build started inside [startMicros, endMicros).
List<FrameSample> framesInWindow(
  Iterable<FrameSample> samples,
  int startMicros,
  int endMicros,
) => [
  for (final s in samples)
    if (s.buildStart >= startMicros && s.buildStart < endMicros) s,
];

/// Rounds to [digits] decimals for the log.
double roundTo(double value, [int digits = 2]) {
  if (!value.isFinite) return value;
  final f = math.pow(10, digits).toDouble();
  return (value * f).roundToDouble() / f;
}

/// One `BENCH {...}` line. Non-finite numbers become null so the line stays
/// valid JSON.
String benchLine(Map<String, Object?> fields, {String tag = 'BENCH'}) {
  final clean = <String, Object?>{
    for (final e in fields.entries)
      e.key: (e.value is double && !(e.value! as double).isFinite)
          ? null
          : e.value,
  };
  return '$tag ${jsonEncode(clean)}';
}
