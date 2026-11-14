// The odds of trapping and of the cast (task T18). EVERY WEIGHT HERE IS A
// GAME CHOICE: no source measures what gear, ground, month or hour does to a
// trapper's luck (research section 8, "No source gives what each item
// changes in the odds"). The season's ends are the owner's word of 14 Nov
// 2026 («الضعف: المبتدي طير كل 6 مواسم تقريباً، والمجهز زين موسمين من كل
// 3»), twice the sources' range of one season in 12.5 to one in 2.98
// (40 birds over 500 to 119 trappers [211][213]): a GAME CHOICE THAT DEPARTS
// FROM THE SOURCES, measured by tool/trap_odds.dart.
//
// The day's falcon is drawn from the world's seed, the day and the ground
// (never stored): the same day gives the same falcon however often he looks,
// and no draw depends on what he did before (no pity timer, no help).
import '../catalog/falconry.dart';
import '../common/rng.dart';
import '../common/time.dart';

/// The falcon that passes his ground on a day, if one does.
class Passer {
  const Passer(this.window, this.species, this.farkh);
  final TrapWindow window;
  final FalconSpecies species;

  /// A bird of the year (فرخ); else a قرناس.
  final bool farkh;

  bool get sellable => species == FalconSpecies.passagePeregrine && farkh;
}

class TrapOdds {
  const TrapOdds._();

  /// A falcon passes a trapping ground on a day in October on the coast
  /// with this chance; the north and the south inland pass fewer (the coasts
  /// best «بلا منازع» [204]; the passage in the north in October
  /// [202][203]), November fewer than October (the peak in October [205]).
  /// Chosen so that the best a man can do on a day (every gear, every
  /// window) catches a sellable bird with [bestDay], so that no season of 61
  /// days can pass two in 3 (the owner's «موسمين من كل 3», never beyond).
  static const passCoast = 0.0412;
  // (measured by tool/trap_odds.dart over 20,000 seasons: the bare beginner
  // 0.160, the well equipped 0.647)
  static const groundNorth = 0.8;
  static const groundSouth = 0.6;
  static const november = 0.92;

  /// The best day's chance: 1 − (1/3)^(1/61).
  static const bestDay = 0.01785;

  /// The window the day's falcon comes in: dawn to 10:00 most, the evening
  /// hour little [204].
  static const windows = [0.85, 0.10, 0.05];

  /// What passes: the passage peregrine most [198]; the saker passes the
  /// north [198]; the residents seldom (the shares game choices).
  static List<(FalconSpecies, bool, double)> mix(Ground g) {
    final m = [
      (FalconSpecies.passagePeregrine, true, g.coast ? 0.6 : 0.55),
      (FalconSpecies.passagePeregrine, false, 0.12),
      (FalconSpecies.saker, true, g.north ? 0.14 : 0.06),
      (FalconSpecies.saker, false, g.north ? 0.06 : 0.04),
      (
        FalconSpecies.mountainPeregrine,
        false,
        g.coast && !g.north ? 0.05 : 0.02,
      ),
    ];
    // the lanner, resident inland, the rest (the shares sum to 1)
    final rest = 1.0 - m.fold(0.0, (a, x) => a + x.$3);
    return [...m, (FalconSpecies.lanner, false, rest)];
  }

  static double passChance(Ground g, GameDay day) {
    final ground = g.coast ? 1.0 : (g.north ? groundNorth : groundSouth);
    final month = day.month == 11 ? november : 1.0;
    return passCoast * ground * month;
  }

  /// The day's falcon at [g], or null (none passes, or out of the season).
  static Passer? passer(int seed, Ground g, GameDay day) {
    if (!g.trapping || PermitKind.trapping.seasonOn(day) == null) return null;
    final rng = Rng.keyed(seed, [day.value, 'trapDay', g.name]);
    if (!rng.chance(passChance(g, day))) return null;
    final w = rng.weighted(TrapWindow.values, windows);
    final m = mix(g);
    final pick = rng.weighted(m, [for (final x in m) x.$3]);
    return Passer(w, pick.$1, pick.$2);
  }

  /// He sees the falcon in its window: always with the binoculars, six times
  /// in ten without them [223] (game choices).
  static const spotBinoculars = 1.0;
  static const spotEyes = 0.6;

  /// It takes the lure: a pigeon 0.7, the bird net 0.5; each lure of the
  /// same kind after a refusal half as likely; after [triesMost] refusals it
  /// goes.
  static const takePigeon = 0.7;
  static const takeBirdNet = 0.5;
  static const triesMost = 3;

  /// The net holds it once it has taken the lure; else it stooped and was
  /// not held.
  static const hold = 0.8;

  // --------------------------------------------------------------- the cast

  /// A cast takes its quarry with this chance: from the falcon's own skill
  /// (hidden), the ground and luck (the owner's decision 1: «النتيجة من الصقر
  /// والأرض والحظ»): the stone-curlew in open land, the houbara in the
  /// estate, where the birds are released for it [142] and found more often.
  static double castChance(double skill, Ground? g, Quarry q) {
    final base = q == Quarry.houbara ? 0.15 + 0.45 * skill : 0.2 + 0.5 * skill;
    return g == Ground.estate ? base * 1.2 : base;
  }

  /// Flights a falcon makes in a day (morning and afternoon: game choice).
  static const flightsADay = 3;

  /// A falcon lost on a flight (the owner's decision 6: «يضيع نادر»), and
  /// found when he looks for it: mostly, and more with the tracker («جهاز
  /// التتبع يقلل الخطر»).
  static const lost = 0.02;
  static const foundWithTracker = 0.95;
  static const foundWithout = 0.6;
}
