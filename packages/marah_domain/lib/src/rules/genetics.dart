import '../catalog/catalog.dart';
import '../common/rng.dart';

/// Quantitative genetics for judged traits.
///
/// Each trait has a breeding value (passed on) and a permanent environmental
/// deviation (shown on top). A calf gets the mid-parent breeding value plus
/// Mendelian sampling, partly shared across traits because overall build is
/// correlated, so champions can throw ordinary calves and the reverse.
class Genetics {
  const Genetics._();

  static const populationSd = 8.0;
  static const mendelianSharedSd = 3.4;
  static const mendelianTraitSd = 4.6;
  static const envSharedSd = 2.5;
  static const envTraitSd = 5.0;

  /// Crossing colour families muddies the coat colour.
  static const crossCoatPenalty = 18.0;

  static Map<Trait, double> randomGenes(Rng rng, {required double mean}) => {
    for (final t in Trait.values)
      t: q2(clampDouble(rng.normal(mean: mean, sd: populationSd), 5, 99)),
  };

  static Map<Trait, double> randomEnv(Rng rng) {
    final shared = rng.normal(sd: envSharedSd);
    return {
      for (final t in Trait.values)
        t: q2(clampDouble(shared + rng.normal(sd: envTraitSd), -15, 15)),
    };
  }

  static Map<Trait, double> inherit(
    Rng rng,
    Map<Trait, double> sire,
    Map<Trait, double> dam, {
    required bool crossbred,
  }) {
    final shared = rng.normal(sd: mendelianSharedSd);
    return {
      for (final t in Trait.values)
        t: q2(
          clampDouble(
            (sire[t]! + dam[t]!) / 2 +
                shared +
                rng.normal(sd: mendelianTraitSd) -
                (crossbred && t == Trait.coat ? crossCoatPenalty : 0),
            5,
            99,
          ),
        ),
    };
  }

  /// Same-family parents breed true; a cross takes either parent's family.
  static ColorCategory calfCategory(
    Rng rng,
    ColorCategory sire,
    ColorCategory dam,
  ) => sire == dam ? dam : (rng.chance(0.5) ? dam : sire);
}
