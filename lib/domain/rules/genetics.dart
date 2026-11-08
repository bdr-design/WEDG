import '../../core/rng.dart';
import '../models/catalog.dart';

/// Quantitative genetics for conformation traits.
///
/// Each trait has a breeding value (what is passed on) and a permanent
/// environmental deviation (what the body shows on top of it). A calf gets
/// the mid-parent breeding value plus Mendelian sampling, so champions can
/// throw ordinary calves and the reverse — just as breeders see in practice.
class Genetics {
  /// Spread of breeding values in the general population.
  static const populationSd = 8.0;

  /// Mendelian sampling: sqrt(1/2) × additive SD, split into a part shared
  /// by all traits (overall build is correlated) and a per-trait part.
  static const mendelianSharedSd = 3.4;
  static const mendelianTraitSd = 4.6;

  /// Spread of the permanent environmental deviation (shared + per trait).
  static const envSharedSd = 2.5;
  static const envTraitSd = 5.0;

  /// Genes for a camel from the wider population, centred on [mean].
  static Map<Trait, double> randomGenes(Rng rng, {required double mean}) => {
        for (final t in Trait.values)
          t: clampDouble(rng.gaussian(mean: mean, sd: populationSd), 5, 99),
      };

  static Map<Trait, double> randomEnv(Rng rng) {
    final shared = rng.gaussian(sd: envSharedSd);
    return {
      for (final t in Trait.values)
        t: clampDouble(shared + rng.gaussian(sd: envTraitSd), -15, 15),
    };
  }

  /// Breeding values of a calf from its sire and dam.
  static Map<Trait, double> inherit(
    Rng rng,
    Map<Trait, double> sire,
    Map<Trait, double> dam, {
    required bool crossbred,
  }) {
    final shared = rng.gaussian(sd: mendelianSharedSd);
    return {
      for (final t in Trait.values)
        t: clampDouble(
          (sire[t]! + dam[t]!) / 2 +
              shared +
              rng.gaussian(sd: mendelianTraitSd) -
              // Crossing colour families muddies the coat colour.
              (crossbred && t == Trait.coat ? 18 : 0),
          5,
          99,
        ),
    };
  }

  /// Colour family of a calf. Same-family parents breed true; a cross takes
  /// either parent's family and is recorded as crossbred (خلط).
  static ColorCategory calfCategory(
      Rng rng, ColorCategory sire, ColorCategory dam) {
    if (sire == dam) return dam;
    return rng.chance(0.5) ? dam : sire;
  }
}
