// The three auctions' lots (task T18): worked out from the world's seed and
// the day each time they are asked for, never stored, so a game that never
// looks at them draws nothing and saves nothing new. A lot sold is kept by
// its key in the player's Falconry.lotsGone.
import '../catalog/falconry.dart';
import '../common/rng.dart';
import '../common/time.dart';
import 'hunt_balance.dart';

/// One bird offered at an auction on a day.
class FalconLot {
  const FalconLot({
    required this.route,
    required this.day,
    required this.index,
    required this.species,
    required this.female,
    required this.hatched,
    required this.lengthQ,
    required this.widthQ,
    required this.weightG,
    required this.opening,
    required this.value,
    required this.skill,
    this.ground,
    this.trappedDaysAgo,
  });

  final FalconRoute route;
  final GameDay day;
  final int index;
  final FalconSpecies species;
  final bool female;
  final int hatched;
  final int lengthQ;
  final int widthQ;
  final int weightG;

  /// The opening bid (seen by every bidder).
  final int opening;

  /// HIDDEN: the last rival's bid (the bird's worth tonight).
  final int value;

  /// HIDDEN: how good a hunter it is.
  final double skill;

  /// Where a trapping auction's bird was trapped, and how many days ago
  /// (the sale pages give it [187][216]; the record bird was trapped the
  /// day before [199]).
  final Ground? ground;
  final int? trappedDaysAgo;

  String get key => '${route.name}:${day.value}:$index';
}

class FalconMarket {
  const FalconMarket._();

  /// The lots [route] offers on [day] (none when it is closed).
  static List<FalconLot> lots(int seed, FalconRoute route, GameDay day) {
    if (!route.openOn(day)) return const [];
    final n = HuntBalance.lotsOn(
      route,
      Rng.keyed(seed, [day.value, 'falconLots', route.name]),
    );
    return [for (var i = 0; i < n; i++) _lot(seed, route, day, i)];
  }

  static FalconLot _lot(int seed, FalconRoute route, GameDay day, int i) {
    final rng = Rng.keyed(seed, [day.value, 'falconLot', route.name, i]);
    final year = day.date.year;
    final (species, female, hatched) = switch (route) {
      // farm-bred sakers of the year (the view: «حر فرخ إنتاج مزارع»)
      FalconRoute.breeders => (FalconSpecies.saker, rng.chance(0.5), year),
      // imported sakers, a فرخ or a قرناس (game choice)
      FalconRoute.exhibition => (
        FalconSpecies.saker,
        rng.chance(0.5),
        rng.chance(0.6) ? year : year - 1,
      ),
      // females only for now: every sale read gives a female's size
      // [187][216]; whether a male of the year is taken was not found
      FalconRoute.trapping => (FalconSpecies.passagePeregrine, true, year),
    };
    final (len, wid, g) = HuntBalance.sizeOf(species, female, rng);
    final value = HuntBalance.worthAt(route, rng.nextDouble());
    final opening = HuntBalance.opening(route, value, rng);
    // (dearer birds hunt a little better on the whole: game choice)
    final skill = q(
      HuntBalance.lotSkillBase +
          HuntBalance.lotSkillSpread * rng.nextDouble() +
          HuntBalance.lotSkillByWorth * _rank(route, value),
    );
    final trapped = route == FalconRoute.trapping;
    final grounds = [
      for (final gr in Ground.values)
        if (gr.trapping) gr,
    ];
    return FalconLot(
      route: route,
      day: day,
      index: i,
      species: species,
      female: female,
      hatched: hatched,
      lengthQ: len,
      widthQ: wid,
      weightG: g,
      opening: opening,
      value: value,
      skill: skill,
      ground: trapped ? rng.pick(grounds) : null,
      trappedDaysAgo: trapped
          ? rng.range(1, HuntBalance.trappedDaysMost)
          : null,
    );
  }

  /// Where [value] sits in [route]'s spread, 0 to 1.
  static double _rank(FalconRoute route, int value) {
    final q = HuntBalance.worth[route]!;
    final lo = q.first.$2, hi = q[q.length - 2].$2;
    final r = (value - lo) / (hi - lo);
    return r < 0 ? 0 : (r > 1 ? 1 : r);
  }

  static double q(double v) => (v * 100).roundToDouble() / 100;

  /// A passport's number (game choice: ten digits).
  static String passportNumber(Rng rng) {
    final b = StringBuffer('${rng.range(1, 9)}');
    for (var i = 0; i < 9; i++) {
      b.write(rng.nextInt(10));
    }
    return b.toString();
  }
}
