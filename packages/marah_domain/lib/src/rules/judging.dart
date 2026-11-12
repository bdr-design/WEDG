import '../catalog/catalog.dart';
import '../common/rng.dart';
import '../common/time.dart';
import '../model/camel.dart';

/// What a camel's body shows, and how a judging panel scores it.
class Judging {
  const Judging._();

  /// Features that depend on flesh and care: a thin camel's hump shrinks and
  /// its neck and stance lose fullness.
  static const conditionSensitivity = {
    Trait.hump: 0.45,
    Trait.neck: 0.15,
    Trait.back: 0.15,
    Trait.stance: 0.25,
    Trait.fore: 0.05,
    Trait.hind: 0.05,
    Trait.coat: 0.10,
  };

  static const neutralCondition = 72.0;

  /// What the eye sees for [t] (0–100).
  static double observed(Camel c, Trait t, GameDay today) {
    var v = c.genes[t]! + c.env[t]!;
    v += (c.condition - neutralCondition) * (conditionSensitivity[t] ?? 0);
    if (c.health != HealthStatus.healthy) {
      v -= (t == Trait.stance || t == Trait.coat) ? 6 : 2;
    }
    final years = c.ageYears(today);
    if (years >= 16) v -= (years - 15) * 1.2;
    return clampDouble(v, 0, 100);
  }

  static Map<Trait, double> observedAll(Camel c, GameDay today) => {
    for (final t in Trait.values) t: observed(c, t, today),
  };

  /// Weighted overall look (0–100): the basis of value and judging.
  static double quality(Camel c, GameDay today) {
    var sum = 0.0;
    for (final t in Trait.values) {
      sum += observed(c, t, today) * t.weight;
    }
    return sum;
  }

  /// Breeding-value quality (hidden).
  static double geneticQuality(Map<Trait, double> genes) {
    var sum = 0.0;
    for (final t in Trait.values) {
      sum += genes[t]! * t.weight;
    }
    return sum;
  }

  /// A panel marks each feature out of 10; each judge's eye differs a
  /// little. The round score is the panel average out of 100, plus how the
  /// camel presents on the day.
  static JudgedScore judge(
    Rng rng,
    Map<Trait, double> observed, {
    int judges = 5,
  }) {
    final marks = <Trait, double>{};
    var total = 0.0;
    for (final t in Trait.values) {
      var s = 0.0;
      for (var j = 0; j < judges; j++) {
        s += clampDouble(observed[t]! / 10 + rng.normal(sd: 0.35), 0, 10);
      }
      final mark = s / judges;
      marks[t] = mark;
      total += mark * 10 * t.weight;
    }
    total += rng.normal(sd: 0.6);
    return JudgedScore(clampDouble(total, 0, 100), marks);
  }
}

class JudgedScore {
  const JudgedScore(this.total, this.marks);
  final double total;
  final Map<Trait, double> marks;
}
