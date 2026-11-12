import 'dart:math' as math;

import '../catalog/catalog.dart';
import '../common/money.dart';
import '../common/time.dart';
import '../model/camel.dart';
import 'judging.dart';

/// Market value of a camel.
///
/// An ordinary camel trades near its meat-and-milk value; beauty multiplies
/// that steeply, placings and a confirmed pregnancy from a good bull add to
/// it. All prices are rounded the way they are quoted at the market.
class Valuation {
  const Valuation._();

  /// (field) Price of an average-looking camel by age class.
  static int basePrice(AgeClass a, Sex s) {
    final female = switch (a) {
      AgeClass.hwar || AgeClass.makhlool => 7000,
      AgeClass.mafrood => 10000,
      AgeClass.haq => 13000,
      AgeClass.laqi => 16000,
      AgeClass.jatha => 19000,
      AgeClass.thani => 21000,
      AgeClass.rubaa => 22000,
      AgeClass.sedees => 22000,
      AgeClass.fater || AgeClass.naab || AgeClass.harish => 20000,
    };
    return s == Sex.female ? female : (female * 0.9).round();
  }

  static double qualityMultiplier(double q) {
    if (q >= 50) return math.exp(0.105 * (q - 50));
    return math.max(0.55, math.exp(0.035 * (q - 50)));
  }

  static double placingMultiplier(Camel c) {
    var bonus = 0.0;
    for (final p in c.placings) {
      final place = switch (p.rank) {
        1 => 1.0,
        2 => 0.6,
        3 => 0.4,
        <= 5 => 0.2,
        <= 10 => 0.08,
        _ => 0.0,
      };
      final tier = switch (p.tier) {
        3 => 1.5,
        2 => 0.55,
        _ => 0.2,
      };
      bonus += place * tier;
    }
    return 1 + math.min(bonus, 3.0);
  }

  static Riyal value(Camel c, GameDay today) {
    final q = Judging.quality(c, today);
    var v =
        basePrice(c.ageClass(today), c.sex) *
        qualityMultiplier(q) *
        c.category.baseDemand *
        placingMultiplier(c);
    if (c.pregnancyConfirmed) {
      final sireQ = Judging.geneticQuality(c.pregnancy!.sireGenes);
      v *= 1.1 + math.max(0, (sireQ - 55) / 100);
    }
    if (c.health != HealthStatus.healthy) v *= 0.7;
    if (c.crossbred) v *= 0.8;
    final years = c.ageYears(today);
    if (years >= 15) v *= math.max(0.25, 1 - (years - 14) * 0.08);
    return marketRound(v);
  }

  /// What the market shows the owner: a range, not the exact value.
  static (Riyal, Riyal) estimate(Camel c, GameDay today) {
    final v = value(c, today).value.toDouble();
    return (marketRound(v * 0.88), marketRound(v * 1.12));
  }
}
