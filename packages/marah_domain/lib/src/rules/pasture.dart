import '../catalog/region.dart';
import '../common/rng.dart';
import '../common/time.dart';
import 'balance.dart';

/// Whether a region's grazing is green (the owner, 12 Nov 2026: the herd goes
/// longer without water while it is). A season runs from October, when the
/// rains begin, and each region's season is wet or dry by the world's seed,
/// the same on every device.
class Pasture {
  const Pasture._();

  /// How many times it has been worked out (the tests count it: drawn for
  /// every camel every day, it made a winter day at 10,000 head twice as long).
  static int lookups = 0;

  static bool green(int worldSeed, Region region, GameDay day) {
    lookups++;
    final month = day.month;
    if (!Balance.greenMonths.contains(month)) return false;
    final year = day.date.year;
    final season = month >= 10 ? year : year - 1;
    return Rng.keyed(worldSeed, [
      'pasture',
      region.name,
      season,
    ]).chance(Balance.wetSeasonChance);
  }
}
