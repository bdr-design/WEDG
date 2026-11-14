// The hunting season's numbers (task T18). Each is sourced ("[n]", docs/
// research-realism.md section 8) or a game choice; docs/GDD.md section 13
// lists them all.
import '../catalog/falconry.dart';
import '../common/rng.dart';

class HuntBalance {
  const HuntBalance._();

  /// A falcon's keep (its meat, الدس), by the day: SAR 20 (game choice: the
  /// season's money page, design/hunt/season.cjs; the answers' Q-25).
  static const upkeepPerDay = 20;

  /// Left without الدعو this many days, a falcon steps back a week (the
  /// design's view 8: «لو تركته أسبوعين يرجع خطوة»).
  static const stepBackDays = 14;
  static const stepBack = 7;

  /// A trip of days lasts at most the trapping season's 60 nights (game
  /// choice).
  static const mostNights = 60;

  /// A kept trapped peregrine may be set free from 1 February to 30 April
  /// (the owner's item 19, «مخير بين الاثنين»; the answers' Q-4, PROVISIONAL:
  /// 30 April, the spring passage north, is a game choice).
  static const releaseFrom = (2, 1);
  static const releaseTo = (4, 30);

  /// The falcons' room holds 4 (game choice, the season's design).
  static const roomHolds = 4;

  /// A new falcon wants 4 weeks of الدعو before its first outing (game
  /// choice: the design's view 8; real: September and early October are the
  /// الدعو [155]).
  static const dauDaysNeeded = 28;

  /// The months of the moult (المقيض), when there is no الدعو: May to
  /// August (game choice: the moult's months are not sourced).
  static const moultMonths = {5, 6, 7, 8};

  /// The lots an auction offers in a day: the breeders' auction 4 (game
  /// choice: it sold more than SAR 33 million in 2026 [158], hundreds of
  /// birds; the phone lists a few), the exhibition 2 (game choice), the
  /// trapping auction 0 to 3 a night (game choice: 81 birds in 30 nights in
  /// 2022 [200], 40 in 60 in 2025 [213]).
  static int lotsOn(FalconRoute r, Rng rng) => switch (r) {
    FalconRoute.breeders => 4,
    FalconRoute.exhibition => 2,
    FalconRoute.trapping => rng.weighted([0, 1, 2, 3], [0.2, 0.35, 0.3, 0.15]),
  };

  /// A bird's worth at each route, as quantiles: (share, riyals), read by
  /// linear steps between them. Each point marked:
  /// - the breeders' auction (a farm-bred saker): its median 19,000, «about
  ///   19,000 a bird» [158]; the rest a game choice kept close about it
  ///   (12,000 to 60,000: the 2026 top bird of 1.3 million [158] was a
  ///   Canadian falcon, not a farm-bred saker, and is not this route's);
  /// - the exhibition (an imported saker): its ends the two sales known,
  ///   100,000 and 700,000 [184]; its median 250,000 a game choice between
  ///   them;
  /// - the trapping auction (the passage peregrine of the year): its floor
  ///   50,000 (2022's lowest [200]); 61,000 at 0.1 (2024's lowest [190]);
  ///   71,000 at 0.25 (2025's lowest read [217]); 102,000 the median (the
  ///   sales read, 2025's 112,000 [185][209] over-reporting the dear);
  ///   300,000 at 0.85 (at least 6 of 2025's 40 at 300,000 or more
  ///   [185][211][213]: the floor taken as the share); 361,000 at 0.975 and
  ///   400,000 at 0.995 (the dearest of 2025 and 2024 [216][221]: about one
  ///   bird in 40 above 361,000, as one of 2025's 40); the record 650,000
  ///   [187][199] the end. Its mean is about 145,000: 2025's level (about
  ///   160,000 [213]) more than 2020-25's (about 100,000 [213]); the steps
  ///   between the points are a game choice.
  static const worth = {
    FalconRoute.breeders: [
      (0.0, 12000),
      (0.25, 15000),
      (0.5, 19000),
      (0.75, 24000),
      (0.95, 35000),
      (1.0, 60000),
    ],
    FalconRoute.exhibition: [(0.0, 100000), (0.5, 250000), (1.0, 700000)],
    FalconRoute.trapping: [
      (0.0, 50000),
      (0.1, 61000),
      (0.25, 71000),
      (0.5, 102000),
      (0.7, 158000),
      (0.85, 300000),
      (0.975, 361000),
      (0.995, 400000),
      (1.0, 650000),
    ],
  };

  /// The worth at share [u] of [route]'s spread, to the nearest 1,000.
  static int worthAt(FalconRoute route, double u) {
    final q = worth[route]!;
    for (var i = 1; i < q.length; i++) {
      final (u1, v1) = q[i];
      if (u <= u1) {
        final (u0, v0) = q[i - 1];
        final v = v0 + (v1 - v0) * (u - u0) / (u1 - u0);
        return (v / 1000).round() * 1000;
      }
    }
    return q.last.$2;
  }

  /// The opening bid of a lot worth [value], drawn mostly on its own so
  /// that it tells little of the worth (the answers, phase 2): three times
  /// in four from 30,000 to 50,000 (under every trapping bird's worth: it
  /// tells nothing), else from 50,000 up to 150,000, never above the worth
  /// (a weak tie, measured in the tests); the span 30,000 to 150,000 is the
  /// trapping auction's [217]. At the other two routes the same shares of
  /// their own floor (game choice). To the nearest 5,000 (1,000 under
  /// 20,000).
  static int opening(FalconRoute route, int value, Rng rng) {
    final floor = worth[route]!.first.$2;
    final lo = route == FalconRoute.trapping ? 30000 : floor * 6 ~/ 10;
    final mid = route == FalconRoute.trapping ? 50000 : floor;
    final top = route == FalconRoute.trapping ? 150000 : value;
    final step = value < 20000 ? 1000 : 5000;
    final low = rng.chance(0.75);
    final u = rng.nextDouble();
    final hi = value < top ? value : top;
    final o = low || hi <= mid ? lo + u * (mid - lo) : mid + u * (hi - mid);
    var r = (o / step).floor() * step;
    if (r > value) r = value;
    if (r < step) r = step;
    return r;
  }

  /// A passage peregrine of the year's length and width in quarter inches
  /// and its weight in grams: 15 to 16 inches and 950 to 1,122 g, as the
  /// sales read give them [187][199][209][216] (the spread a game choice);
  /// a male (تبع, at the breeders' and the exhibition only) a third smaller
  /// (game choice: falcons' males are smaller).
  static (int, int, int) sizeOf(FalconSpecies s, bool female, Rng rng) {
    final (lo, hi, glo, ghi) = switch (s) {
      FalconSpecies.saker => (64, 70, 1000, 1300),
      FalconSpecies.passagePeregrine => (60, 64, 940, 1130),
      FalconSpecies.mountainPeregrine => (58, 62, 800, 1000),
      FalconSpecies.lanner => (56, 60, 650, 900),
    };
    final k = female ? 1.0 : 0.75;
    final len = (rng.range(lo, hi) * (female ? 1.0 : 0.85)).round();
    final wid = (rng.range(lo, hi) * (female ? 1.0 : 0.85)).round();
    final g = (rng.range(glo, ghi) * k).round();
    return (len, wid, g);
  }

  /// The days since a trapping auction's lot was trapped: 1 to 5 (game
  /// choice: the record bird was trapped the day before [199], one the
  /// Monday before [187]).
  static const trappedDaysMost = 5;

  /// The falcons' names the game gives (game choice; he may keep them).
  static const names = [
    'سهيل',
    'غيث',
    'براق',
    'ريح',
    'برق',
    'مزن',
    'سهم',
    'نجم',
    'صخر',
    'فهد',
    'شهاب',
    'رعد',
    'وسم',
    'هدّاج',
    'زعزوع',
    'سلطان',
    'نمر',
    'جسور',
    'مطر',
    'عاصف',
  ];
}
