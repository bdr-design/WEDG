import '../catalog/region.dart';
import '../common/ids.dart';
import '../common/money.dart';
import '../common/time.dart';

/// The ration: an adult's dry matter a day and the barley's share of it (the
/// rest alfalfa), and the body condition it holds a camel at. The real intake
/// is 8 to 17 kg of dry matter a day for a 500 kg camel (GDD 4.3); the three
/// rations and their shares are game choices inside it.
enum FeedPlan {
  economy(dryMatterKg: 9, barleyShare: 0.2, conditionTarget: 58),
  standard(dryMatterKg: 11, barleyShare: 0.3, conditionTarget: 74),
  premium(dryMatterKg: 14, barleyShare: 0.45, conditionTarget: 90);

  const FeedPlan({
    required this.dryMatterKg,
    required this.barleyShare,
    required this.conditionTarget,
  });
  final double dryMatterKg;
  final double barleyShare;
  final int conditionTarget;
}

/// What the farm buys and keeps (GDD 4.3; the owner's decision of 12 Nov 2026:
/// feed and water run out and are ordered). Barley comes in 50 kg bags,
/// alfalfa in bales, water by the tanker load (الوايت).
enum Supply { barley, alfalfa, water }

/// An order on its way to the farm.
class Delivery {
  const Delivery({
    required this.supply,
    required this.units,
    required this.arrivesOn,
  });
  final Supply supply;
  final int units;
  final GameDay arrivesOn;

  Map<String, Object?> toJson() => {
    'supply': supply.name,
    'units': units,
    'arrivesOn': arrivesOn.value,
  };

  static Delivery fromJson(Map<String, Object?> j) => Delivery(
    supply: Supply.values.byName(j['supply']! as String),
    units: j['units']! as int,
    arrivesOn: GameDay(j['arrivesOn']! as int),
  );
}

/// The player's farm (العزبة).
class Farm {
  Farm({
    required this.name,
    required this.region,
    required this.capacity,
    required this.shepherds,
    required this.feedPlan,
    this.storeKg = 0,
    this.tankL = 0,
    this.barleyKg = 0,
    this.alfalfaKg = 0,
    this.waterL = 0,
    this.dryDays = 0,
    this.fedShare = 1,
    List<Delivery>? deliveries,
    Set<Supply>? short,
  }) : deliveries = deliveries ?? [],
       short = short ?? {};

  String name;
  Region region;
  int capacity;
  int shepherds;

  /// The ration: how much of the stores each camel is fed a day.
  FeedPlan feedPlan;

  /// The feed store's and the water tank's sizes.
  int storeKg;
  int tankL;

  /// What is in them.
  double barleyKg;
  double alfalfaKg;
  double waterL;

  /// Days in a row the herd has gone without enough water.
  int dryDays;

  /// The share of the ration the herd got today (1: all of it).
  double fedShare;

  /// The supplies that did not cover the day's need (each warned of once,
  /// the day it went short, until it covers the need again).
  final Set<Supply> short;
  final List<Delivery> deliveries;

  Map<String, Object?> toJson() => {
    'name': name,
    'region': region.name,
    'capacity': capacity,
    'shepherds': shepherds,
    'feedPlan': feedPlan.name,
    'storeKg': storeKg,
    'tankL': tankL,
    'barleyKg': barleyKg,
    'alfalfaKg': alfalfaKg,
    'waterL': waterL,
    'dryDays': dryDays,
    'fedShare': fedShare,
    'short': [
      for (final s in Supply.values)
        if (short.contains(s)) s.name,
    ],
    'deliveries': [for (final d in deliveries) d.toJson()],
  };

  static Farm fromJson(Map<String, Object?> j) => Farm(
    name: j['name']! as String,
    region: Region.values.byName(j['region']! as String),
    capacity: j['capacity']! as int,
    shepherds: j['shepherds']! as int,
    feedPlan: FeedPlan.values.byName(j['feedPlan']! as String),
    storeKg: j['storeKg']! as int,
    tankL: j['tankL']! as int,
    barleyKg: (j['barleyKg']! as num).toDouble(),
    alfalfaKg: (j['alfalfaKg']! as num).toDouble(),
    waterL: (j['waterL']! as num).toDouble(),
    dryDays: j['dryDays']! as int,
    fedShare: (j['fedShare']! as num).toDouble(),
    short: {
      for (final s in j['short']! as List<Object?>)
        Supply.values.byName(s! as String),
    },
    deliveries: [
      for (final d in j['deliveries']! as List<Object?>)
        Delivery.fromJson(d! as Map<String, Object?>),
    ],
  );
}

enum LedgerCategory {
  opening,
  purchase,
  sale,
  feed,
  water,
  wages,
  vet,
  transport,
  prize,
  studFee,
  commission,
  construction,
}

/// One money movement. Recurring costs (feed, wages) are kept as one row per
/// category per month, updated in place, so the ledger stays small while
/// cash always equals the sum of all rows.
class LedgerEntry {
  LedgerEntry({
    required this.day,
    required this.category,
    required this.amount,
    this.ref,
    this.month,
  });

  final GameDay day;
  final LedgerCategory category;
  Riyal amount;

  /// What the entry is about (a camel id, festival id...), for the UI.
  final String? ref;

  /// Set on monthly roll-up rows: 'YYYY-MM'.
  final String? month;

  Map<String, Object?> toJson() => {
    'day': day.value,
    'cat': category.name,
    'amount': amount.value,
    'ref': ref,
    'month': month,
  };

  static LedgerEntry fromJson(Map<String, Object?> j) => LedgerEntry(
    day: GameDay(j['day']! as int),
    category: LedgerCategory.values.byName(j['cat']! as String),
    amount: Riyal(j['amount']! as int),
    ref: j['ref'] as String?,
    month: j['month'] as String?,
  );
}

/// What belongs to one player: identity, money and farm. Camels live in the
/// world registry and point back with their owner id.
class PlayerState {
  PlayerState({
    required this.id,
    required this.name,
    required this.cash,
    required this.farm,
    required this.favourite,
    List<LedgerEntry>? ledger,
  }) : ledger = ledger ?? [];

  final OwnerId id;
  String name;
  Riyal cash;
  final Farm farm;

  /// The colour family the player chose to specialise in (name only here;
  /// see ColorCategory).
  final String favourite;
  final List<LedgerEntry> ledger;

  Map<String, Object?> toJson() => {
    'id': id.value,
    'name': name,
    'cash': cash.value,
    'farm': farm.toJson(),
    'favourite': favourite,
    'ledger': [for (final l in ledger) l.toJson()],
  };

  static PlayerState fromJson(Map<String, Object?> j) => PlayerState(
    id: OwnerId(j['id']! as String),
    name: j['name']! as String,
    cash: Riyal(j['cash']! as int),
    farm: Farm.fromJson(j['farm']! as Map<String, Object?>),
    favourite: j['favourite']! as String,
    ledger: [
      for (final l in j['ledger']! as List<Object?>)
        LedgerEntry.fromJson(l! as Map<String, Object?>),
    ],
  );
}
