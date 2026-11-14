import '../catalog/catalog.dart';
import '../common/ids.dart';
import '../common/rng.dart';
import '../common/time.dart';
import '../model/camel.dart';
import '../model/game_state.dart';
import '../model/player.dart';
import 'balance.dart';
import 'eligibility.dart';

/// A nursing camel's milk (GDD 12.1; the owner's decisions of 13 Nov 2026):
/// what she gives a day, what her calf keeps, and what is sold to the buyer
/// who comes each day.
abstract final class Milk {
  /// Days since [c] calved while she is in milk (a year from calving), or
  /// null.
  static int? inMilkDays(Camel c, GameDay today) {
    if (c.sex != Sex.female || !c.isAlive || c.lastCalvedOn == null) {
      return null;
    }
    final d = today.daysSince(c.lastCalvedOn!);
    return d >= 0 && d < Balance.lactationDays ? d : null;
  }

  /// [c]'s own level of milk (litres a day; the lactation's shape scales it
  /// from 0.85 up to 1.2 and down to 0.5), fixed for the camel: drawn from
  /// her id, مجاهيم a quarter more.
  static double level(Camel c, int seed) {
    final u = Rng.keyed(seed, ['milk', c.id.value]).nextDouble();
    final base =
        Balance.milkLevelMin +
        (Balance.milkLevelMax - Balance.milkLevelMin) * u;
    return c.category == ColorCategory.majaheem
        ? base * Balance.majaheemMilk
        : base;
  }

  /// The lactation's shape on day [d]: up from 0.85 to 1.2 by the peak, then
  /// down to 0.5 at the year's end.
  static double shape(int d) {
    if (d <= Balance.milkPeakDay) {
      return 0.85 + 0.35 * d / Balance.milkPeakDay;
    }
    final t =
        (d - Balance.milkPeakDay) /
        (Balance.lactationDays - Balance.milkPeakDay);
    return 1.2 - 0.7 * t;
  }

  /// Litres [c] gives today, as fed and watered today: a short ration cuts it
  /// by its share, a dry day by half.
  static double litres(Camel c, Farm farm, GameDay today, int seed) {
    final d = inMilkDays(c, today);
    if (d == null) return 0;
    // (the dawn's ration and water: a rushed delivery later in the day does
    // not change the milk the day gave, the second review's N1)
    final r = farm.today;
    final dawn = r != null && r.day == today;
    var l = level(c, seed) * shape(d) * (dawn ? r.fedAtDawn : farm.fedShare);
    if ((dawn ? r.dryAtDawn : farm.dryDays) > 0) l *= 0.5;
    return l;
  }

  /// Each nursing camel's calf in [herd] while it still suckles, by the
  /// dam's id (one pass: at 10,000 head a search per dam was millions of
  /// checks a day). A dam without one (sold, dead or weaned) has all her milk
  /// sold.
  static Map<CamelId, Camel> calves(Iterable<Camel> herd, GameDay today) {
    final byDam = <CamelId, Camel>{};
    for (final c in herd) {
      final dam = c.dam;
      if (dam != null && c.ageDays(today) < Balance.lactationDays) {
        byDam[dam.id] = c;
      }
    }
    return byDam;
  }

  /// [c] is a calf still suckling its mother, on its owner's farm: a حوار
  /// whatever its age class says (the owner, 13 Nov 2026: «حوار لين ينفطم»;
  /// مخلول is one weaned with الخلال, GDD 5.2), until its first year.
  static bool suckling(Camel c, WorldState w, GameDay today) {
    final ref = c.dam;
    if (ref == null || !c.isAlive) return false;
    if (c.ageDays(today) >= Balance.lactationDays) return false;
    final dam = w.camels[ref.id];
    return dam != null &&
        dam.isAlive &&
        dam.ownerId == c.ownerId &&
        dam.lastCalvedOn == c.born;
  }

  /// The day's milk on [owner]'s farm: each nursing camel's litres, what
  /// her calf keeps and what is sold (one bought today is milked from
  /// tomorrow, when the truck brings her).
  static List<MilkToday> today(
    WorldState w,
    OwnerId owner,
    Farm farm,
    GameDay today,
  ) {
    final herd = w.aliveOwnedBy(owner).toList();
    final byDam = calves(herd, today);
    return [
      for (final c in herd)
        if (!Eligibility.onTheWay(c, today))
          if (inMilkDays(c, today) case final d?)
            () {
              final l = litres(c, farm, today, w.seed);
              final calf = byDam[c.id];
              final own = calf != null && calf.born == c.lastCalvedOn;
              final kept = own ? l * farm.calfShare.part : 0.0;
              return MilkToday(
                camel: c,
                days: d,
                calf: own ? calf : null,
                litres: l,
                sold: l - kept,
              );
            }(),
    ];
  }
}

/// One nursing camel's milk today.
class MilkToday {
  const MilkToday({
    required this.camel,
    required this.days,
    required this.calf,
    required this.litres,
    required this.sold,
  });
  final Camel camel;

  /// Days since she calved.
  final int days;
  final Camel? calf;
  final double litres;
  final double sold;
}
