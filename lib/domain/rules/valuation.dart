import 'dart:math' as math;

import '../models/camel.dart';
import '../models/catalog.dart';
import 'judging.dart';

/// Market value of a camel in riyals.
///
/// An ordinary camel trades near its meat and milk value (roughly 8–25 thousand
/// riyals by age). Beauty multiplies that steeply: a strong mazayen camel is
/// worth hundreds of thousands, a proven champion millions. Contest placings
/// and a confirmed pregnancy from a good bull add to it.
class Valuation {
  /// Price of an average-looking camel by age class.
  static int basePrice(AgeClass a, Sex s) {
    final female = switch (a) {
      AgeClass.hwar => 7000,
      AgeClass.mafrood => 10000,
      AgeClass.laqi => 13000,
      AgeClass.haq => 16000,
      AgeClass.jatha => 19000,
      AgeClass.thani => 21000,
      AgeClass.rubaa => 22000,
      AgeClass.sedees => 22000,
      AgeClass.mature => 20000,
    };
    return s == Sex.female ? female : (female * 0.9).round();
  }

  static double qualityMultiplier(double q) {
    if (q >= 50) return math.exp(0.105 * (q - 50));
    return math.max(0.55, math.exp(0.035 * (q - 50)));
  }

  static double titleMultiplier(Camel c) {
    var bonus = 0.0;
    for (final t in c.titles) {
      final placing = switch (t.rank) {
        1 => 1.0,
        2 => 0.6,
        3 => 0.4,
        <= 5 => 0.2,
        <= 10 => 0.08,
        _ => 0.0,
      };
      final tier = switch (t.tier) { 3 => 1.5, 2 => 0.55, _ => 0.2 };
      bonus += placing * tier;
    }
    return 1 + math.min(bonus, 3.0);
  }

  static int value(Camel c, int today) {
    final q = Judging.quality(c, today);
    var v = basePrice(c.ageClass(today), c.sex) *
        qualityMultiplier(q) *
        c.category.baseDemand *
        titleMultiplier(c);

    if (c.isPregnantConfirmed) {
      final sireQ = Judging.geneticQuality(c.pregnancy!.sireGenes);
      v *= 1.1 + math.max(0, (sireQ - 55) / 100);
    }
    if (c.health != HealthStatus.healthy) v *= 0.7;
    if (c.crossbred) v *= 0.8;
    final years = c.ageYears(today);
    if (years >= 15) v *= math.max(0.25, 1 - (years - 14) * 0.08);

    return _round(v);
  }

  /// Rounds to a price people would actually quote.
  static int _round(double v) {
    if (v >= 1000000) return (v / 50000).round() * 50000;
    if (v >= 100000) return (v / 5000).round() * 5000;
    if (v >= 10000) return (v / 500).round() * 500;
    return (v / 100).round() * 100;
  }

  static int roundPrice(double v) => _round(v);

  /// The player sees an estimate, not the exact value (السوق يقدّر).
  static (int, int) estimateRange(Camel c, int today) {
    final v = value(c, today);
    return (_round(v * 0.88), _round(v * 1.12));
  }
}
