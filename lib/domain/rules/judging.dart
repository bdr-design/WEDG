import '../../core/rng.dart';
import '../models/camel.dart';
import '../models/catalog.dart';

/// How a camel's body shows each judged feature, and how a panel scores it.
class Judging {
  /// Features that depend on flesh and care: an underfed camel's hump
  /// shrinks and its neck and stance lose fullness.
  static const _conditionSensitivity = {
    Trait.hump: 0.45,
    Trait.neck: 0.15,
    Trait.back: 0.15,
    Trait.stance: 0.25,
    Trait.legs: 0.05,
    Trait.coat: 0.10,
  };

  /// What the eye sees for [t] (0–100): breeding value + permanent
  /// deviation, adjusted for body condition, illness and old age.
  static double phenotype(Camel c, Trait t, int today) {
    var v = c.genes[t]! + c.env[t]!;
    v += (c.condition - 72) * (_conditionSensitivity[t] ?? 0);
    if (c.health != HealthStatus.healthy) {
      v -= (t == Trait.stance || t == Trait.coat) ? 6 : 2;
    }
    final years = c.ageYears(today);
    if (years >= 16) v -= (years - 15) * 1.2;
    return clampDouble(v, 0, 100);
  }

  static Map<Trait, double> phenotypes(Camel c, int today) =>
      {for (final t in Trait.values) t: phenotype(c, t, today)};

  /// Weighted overall quality (0–100), the basis of value and judging.
  static double quality(Camel c, int today) {
    var sum = 0.0;
    for (final t in Trait.values) {
      sum += phenotype(c, t, today) * t.weight;
    }
    return sum;
  }

  /// Breeding-value quality (hidden): what the camel tends to pass on.
  static double geneticQuality(Map<Trait, double> genes) {
    var sum = 0.0;
    for (final t in Trait.values) {
      sum += genes[t]! * t.weight;
    }
    return sum;
  }

  /// A judging panel scores each feature out of 10. Each judge's eye differs
  /// a little; the round score is the panel average out of 100.
  static JudgedScore judge(
    Rng rng,
    Map<Trait, double> phen, {
    int judges = 5,
  }) {
    final marks = <Trait, double>{};
    var total = 0.0;
    for (final t in Trait.values) {
      var s = 0.0;
      for (var j = 0; j < judges; j++) {
        s += clampDouble(phen[t]! / 10 + rng.gaussian(sd: 0.35), 0, 10);
      }
      final mark = s / judges;
      marks[t] = mark;
      total += mark * 10 * t.weight;
    }
    // Presentation on the day (handling, calm in the ring).
    total += rng.gaussian(sd: 0.6);
    return JudgedScore(clampDouble(total, 0, 100), marks);
  }

  /// Plain-language grade for a feature or overall score (0–100).
  static String grade(double v) {
    if (v >= 88) return 'استثنائي';
    if (v >= 78) return 'ممتاز';
    if (v >= 68) return 'جيد جدًا';
    if (v >= 58) return 'جيد';
    if (v >= 48) return 'متوسط';
    return 'ضعيف';
  }
}

class JudgedScore {
  const JudgedScore(this.total, this.marks);
  final double total;
  final Map<Trait, double> marks;
}
