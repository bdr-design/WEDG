/// Deterministic random numbers that give the same results on every
/// platform (Dart VM on iOS/Android, JavaScript on the web, a server).
///
/// * Integer-only core (mulberry32 with 32-bit multiply), so the stream is
///   bit-identical everywhere.
/// * No `log`/`cos`/`exp` in sampling: normal values use the Irwin–Hall sum,
///   which only adds exact doubles.
/// * [Rng.keyed] derives an independent stream from a seed and a key such as
///   `('judge', festivalId, roundId)`. Adding a random draw in one system does
///   not shift the outcomes of any other system.
class Rng {
  Rng(int seed) : _state = seed & 0xFFFFFFFF;

  /// Independent stream for [seed] and the given key parts.
  factory Rng.keyed(int seed, List<Object> key) => Rng(hashKey(seed, key));

  int _state;

  /// FNV-1a over the seed's four bytes and the key's text, 32-bit. (It began
  /// from the seed XORed into the offset basis, and the seed's first byte,
  /// added next, cancelled its own low byte: seeds 1, 2 and 200 drew the same
  /// streams for every key without an id, the review of 57ab698.)
  static int hashKey(int seed, List<Object> key) {
    var h = 0x811C9DC5;
    void add(int byte) {
      h ^= byte & 0xFF;
      h = _imul(h, 0x01000193);
    }

    for (var i = 0; i < 4; i++) {
      add(seed >> (8 * i));
    }
    for (final part in key) {
      for (final unit in part.toString().codeUnits) {
        add(unit);
        add(unit >> 8);
      }
      add(0x1F); // separator
    }
    return h & 0xFFFFFFFF;
  }

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
    if (max <= 0) throw ArgumentError.value(max, 'max', 'must be positive');
    return nextUint32() % max;
  }

  /// Uniform int in [min, max] inclusive.
  int range(int min, int max) => min + nextInt(max - min + 1);

  double rangeDouble(double min, double max) =>
      min + nextDouble() * (max - min);

  bool chance(double p) => nextDouble() < p;

  /// Approximately normal (Irwin–Hall, 12 uniforms). Tails are cut at ±6 sd,
  /// which is what a game wants anyway.
  double normal({double mean = 0, double sd = 1}) {
    var sum = 0.0;
    for (var i = 0; i < 12; i++) {
      sum += nextDouble();
    }
    return mean + (sum - 6.0) * sd;
  }

  T pick<T>(List<T> items) => items[nextInt(items.length)];

  T weighted<T>(List<T> items, List<double> weights) {
    if (items.isEmpty || items.length != weights.length) {
      throw ArgumentError('items and weights must match and not be empty');
    }
    final total = weights.fold<double>(0, (a, b) => a + b);
    var r = nextDouble() * total;
    for (var i = 0; i < items.length; i++) {
      r -= weights[i];
      if (r < 0) return items[i];
    }
    return items.last;
  }

  List<T> shuffled<T>(List<T> items) {
    final list = [...items];
    for (var i = list.length - 1; i > 0; i--) {
      final j = nextInt(i + 1);
      final t = list[i];
      list[i] = list[j];
      list[j] = t;
    }
    return list;
  }
}

double clampDouble(double v, double min, double max) =>
    v < min ? min : (v > max ? max : v);

/// Rounds to 2 decimals. Stored traits and condition are kept at this
/// precision in memory, so saves stay small and a save/load is exact.
double q2(double v) => (v * 100).roundToDouble() / 100;
