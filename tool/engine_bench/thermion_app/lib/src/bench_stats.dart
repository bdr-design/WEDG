import 'dart:convert';

/// Nearest-rank percentile of [samples] (any order), or null when empty.
double? percentile(List<double> samples, double p) {
  if (samples.isEmpty) return null;
  final sorted = List<double>.of(samples)..sort();
  final rank = (p / 100 * sorted.length).ceil().clamp(1, sorted.length);
  return sorted[rank - 1];
}

/// Rounds to [digits] decimals so the BENCH lines stay short.
double? round(double? value, [int digits = 2]) {
  if (value == null || !value.isFinite) return null;
  return double.parse(value.toStringAsFixed(digits));
}

/// One timed sample: when it started (Timeline clock, µs) and how long it
/// took (µs).
class TimedSample {
  const TimedSample(this.startUs, this.durationUs);
  final int startUs;
  final int durationUs;
}

/// Samples whose start lies in [fromUs, toUs), as durations in milliseconds.
List<double> durationsInWindow(
  Iterable<TimedSample> samples,
  int fromUs,
  int toUs,
) => [
  for (final s in samples)
    if (s.startUs >= fromUs && s.startUs < toUs) s.durationUs / 1000.0,
];

/// Formats one benchmark result line exactly as the README asks:
/// `BENCH {"engine":...,...}` with keys in insertion order.
String benchLine(Map<String, Object?> fields) => 'BENCH ${jsonEncode(fields)}';

/// The per-N result line.
String measurementLine({
  required String engine,
  required int n,
  required List<double> frameMs,
  required double windowSeconds,
  required double rssMb,
  List<double> engineMs = const [],
  Map<String, Object?> extra = const {},
}) {
  return benchLine({
    'engine': engine,
    'n': n,
    'frames': frameMs.length,
    'fps': round(frameMs.length / windowSeconds, 1),
    'p50_ms': round(percentile(frameMs, 50)),
    'p90_ms': round(percentile(frameMs, 90)),
    'p99_ms': round(percentile(frameMs, 99)),
    'rss_mb': round(rssMb, 1),
    'engine_p50_ms': round(percentile(engineMs, 50)),
    'engine_p90_ms': round(percentile(engineMs, 90)),
    'engine_p99_ms': round(percentile(engineMs, 99)),
    'engine_frames': engineMs.length,
    ...extra,
  });
}
