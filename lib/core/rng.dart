import 'dart:math' as math;

/// Deterministic, serialisable pseudo-random generator (mulberry32).
///
/// Uses only 32-bit integer maths so it produces the same sequence on the
/// Dart VM (iOS/Android) and on the web, and its whole state is one int that
/// is stored in the save file.
class Rng {
  Rng(int seed) : _state = seed & 0xFFFFFFFF;

  int _state;
  int get state => _state;

  static int _imul(int a, int b) {
    final ah = (a >> 16) & 0xFFFF;
    final al = a & 0xFFFF;
    final bh = (b >> 16) & 0xFFFF;
    final bl = b & 0xFFFF;
    return ((al * bl) + (((ah * bl + al * bh) << 16) & 0xFFFFFFFF)) &
        0xFFFFFFFF;
  }

  /// Next unsigned 32-bit value.
  int nextUint32() {
    _state = (_state + 0x6D2B79F5) & 0xFFFFFFFF;
    var t = _state;
    t = _imul(t ^ (t >> 15), t | 1);
    t = (t ^ (t + _imul(t ^ (t >> 7), t | 61))) & 0xFFFFFFFF;
    return (t ^ (t >> 14)) & 0xFFFFFFFF;
  }

  /// Uniform double in [0, 1).
  double nextDouble() => nextUint32() / 4294967296.0;

  /// Uniform int in [0, max).
  int nextInt(int max) {
    assert(max > 0);
    return (nextDouble() * max).floor();
  }

  /// Uniform int in [min, max] inclusive.
  int range(int min, int max) => min + nextInt(max - min + 1);

  /// Uniform double in [min, max).
  double rangeDouble(double min, double max) =>
      min + nextDouble() * (max - min);

  bool chance(double p) => nextDouble() < p;

  /// Normally distributed value (Box–Muller).
  double gaussian({double mean = 0, double sd = 1}) {
    var u1 = nextDouble();
    if (u1 < 1e-12) u1 = 1e-12;
    final u2 = nextDouble();
    final z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2 * math.pi * u2);
    return mean + z * sd;
  }

  T pick<T>(List<T> items) => items[nextInt(items.length)];

  /// Picks an item using the given non-negative weights.
  T weighted<T>(List<T> items, List<double> weights) {
    assert(items.length == weights.length && items.isNotEmpty);
    final total = weights.fold<double>(0, (a, b) => a + b);
    var r = nextDouble() * total;
    for (var i = 0; i < items.length; i++) {
      r -= weights[i];
      if (r < 0) return items[i];
    }
    return items.last;
  }
}

double clampDouble(double v, double min, double max) =>
    v < min ? min : (v > max ? max : v);
