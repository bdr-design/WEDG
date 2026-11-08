import 'dart:math' as math;

/// Where one camel stands, which way it faces and where its walk cycle starts.
class CamelPlacement {
  const CamelPlacement({
    required this.x,
    required this.z,
    required this.heading,
    required this.clipOffset,
  });

  /// Metres east of the yard (x axis).
  final double x;

  /// Metres south of the yard (z axis).
  final double z;

  /// Rotation about +y in radians, in [0, 2π).
  final double heading;

  /// Start time inside the walk clip in seconds, in [0, clipDuration).
  final double clipOffset;
}

/// Grid spacing from the benchmark README.
const double kHerdSpacing = 4.0;

/// Each camel is moved up to this far (metres) from its grid slot on x and z.
const double kHerdJitter = 1.0;

/// The jittered grid of the engine benchmark: [n] camels, [spacing] metres
/// apart, centred on the origin, each with a random heading and its own clip
/// time offset. Deterministic for a given [seed], so every run and every
/// engine sees the same herd.
List<CamelPlacement> herdLayout(
  int n, {
  required double clipDuration,
  double spacing = kHerdSpacing,
  double jitter = kHerdJitter,
  int seed = 20261108,
}) {
  if (n <= 0) return const [];
  final cols = math.sqrt(n).ceil();
  final rows = (n / cols).ceil();
  final random = math.Random(seed);
  return List<CamelPlacement>.generate(n, (i) {
    final col = i % cols;
    final row = i ~/ cols;
    // Four draws per camel, always in this order.
    final jx = (random.nextDouble() * 2 - 1) * jitter;
    final jz = (random.nextDouble() * 2 - 1) * jitter;
    final heading = random.nextDouble() * 2 * math.pi;
    final offset = random.nextDouble() * clipDuration;
    return CamelPlacement(
      x: (col - (cols - 1) / 2) * spacing + jx,
      z: (row - (rows - 1) / 2) * spacing + jz,
      heading: heading,
      clipOffset: offset,
    );
  }, growable: false);
}
