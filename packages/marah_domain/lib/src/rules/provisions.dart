import '../catalog/catalog.dart';
import '../catalog/region.dart';
import '../common/time.dart';
import '../model/camel.dart';
import '../model/player.dart';
import 'balance.dart';

/// The herd's daily needs and what supplies cost (GDD 4.3; Balance's
/// provisions numbers, each marked field or balance).
class Provisions {
  const Provisions._();

  /// Kilograms or litres in one unit ordered: a bag, a bale, a tanker load.
  static int unitSize(Supply s) => switch (s) {
    Supply.barley => Balance.barleyBagKg,
    Supply.alfalfa => Balance.alfalfaBaleKg,
    Supply.water => Balance.waterLoadL,
  };

  /// Litres a [tanker] carries, and what it costs (the large is the water's
  /// unit; Balance).
  static int tankerSize(Tanker tanker) => switch (tanker) {
    Tanker.large => Balance.waterLoadL,
    Tanker.small => Balance.smallWaterLoadL,
  };

  static double tankerPrice(Tanker tanker) => switch (tanker) {
    Tanker.large => Balance.waterLoadPrice,
    Tanker.small => Balance.smallWaterLoadPrice,
  };

  /// What one unit costs delivered to a farm in [region] (feed by the
  /// region's feed factor; water the same everywhere), in whole riyals as a
  /// supplier asks: the price the player sees times the units is the charge.
  static double unitPrice(Supply s, Region region) => switch (s) {
    Supply.barley => Balance.barleyBagPrice * region.feed,
    Supply.alfalfa => Balance.alfalfaBalePrice * region.feed,
    Supply.water => Balance.waterLoadPrice,
  }.roundToDouble();

  /// A camel's water a day: a nursing camel 42 L; others by the season, a
  /// calf by its age (a suckling calf drinks its dam's milk).
  static double waterFor(Camel c, GameDay today) {
    final nursing =
        c.sex == Sex.female &&
        c.lastCalvedOn != null &&
        today.daysSince(c.lastCalvedOn!) < 365;
    if (nursing) return Balance.nursingWaterL;
    return Balance.waterL(today.month) *
        Balance.feedAgeFactor(c.ageDays(today));
  }

  /// The herd's needs a day under [plan]: barley and alfalfa in kilograms as
  /// delivered (the ration's dry matter over each feed's dry share), water L.
  static ({double barley, double alfalfa, double water}) needs(
    Iterable<Camel> herd,
    FeedPlan plan,
    GameDay today,
  ) {
    var dryMatter = 0.0, water = 0.0;
    for (final c in herd) {
      dryMatter += plan.dryMatterKg * Balance.feedAgeFactor(c.ageDays(today));
      water += waterFor(c, today);
    }
    return (
      barley: dryMatter * plan.barleyShare / Balance.barleyDryMatter,
      alfalfa: dryMatter * (1 - plan.barleyShare) / Balance.alfalfaDryMatter,
      water: water,
    );
  }

  /// Kilograms of feed, as delivered, a grown head eats a day under [plan].
  static double asFedKg(FeedPlan plan) =>
      plan.dryMatterKg * plan.barleyShare / Balance.barleyDryMatter +
      plan.dryMatterKg * (1 - plan.barleyShare) / Balance.alfalfaDryMatter;

  /// What a day's feed costs at [needs] in [region] (water is paid by the
  /// tanker, not by the day).
  static double feedCost(
    ({double barley, double alfalfa, double water}) needs,
    Region region,
  ) =>
      needs.barley / Balance.barleyBagKg * unitPrice(Supply.barley, region) +
      needs.alfalfa / Balance.alfalfaBaleKg * unitPrice(Supply.alfalfa, region);

  /// What is in store, or on order, of [s] (kg or L).
  static double stocked(Farm f, Supply s, {bool withOrders = true}) {
    var v = switch (s) {
      Supply.barley => f.barleyKg,
      Supply.alfalfa => f.alfalfaKg,
      Supply.water => f.waterL,
    };
    if (withOrders) {
      for (final d in f.deliveries) {
        if (d.supply == s) v += d.units * d.size;
      }
    }
    return v;
  }

  /// Room left (kg or L): the feed store holds barley and alfalfa together.
  static double room(Farm f, Supply s) => s == Supply.water
      ? f.tankL - stocked(f, Supply.water)
      : f.storeKg - stocked(f, Supply.barley) - stocked(f, Supply.alfalfa);

  /// Whole days a store lasts at [need] a day (null when nothing is needed).
  static int? daysLeft(double stock, double need) =>
      need <= 0 ? null : (stock / need).floor();
}
