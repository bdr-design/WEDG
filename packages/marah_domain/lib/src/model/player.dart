import '../catalog/catalog.dart';
import '../catalog/region.dart';
import '../common/ids.dart';
import '../common/money.dart';
import '../common/time.dart';
import '../rules/balance.dart';

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

/// The water tankers a farm orders (الوايت): litres and price in Balance.
/// The large is the supply's unit; the small tops up a tank the large one
/// does not fit (the owner, 12 Nov 2026).
enum Tanker { large, small }

/// An order on its way to the farm.
class Delivery {
  const Delivery({
    required this.supply,
    required this.units,
    required this.arrivesOn,
    required this.size,
  });
  final Supply supply;
  final int units;
  final GameDay arrivesOn;

  /// Kilograms or litres in each unit (a small tanker's load is not the
  /// supply's own unit).
  final int size;

  Map<String, Object?> toJson() => {
    'supply': supply.name,
    'units': units,
    'arrivesOn': arrivesOn.value,
    'size': size,
  };

  static Delivery fromJson(Map<String, Object?> j) => Delivery(
    supply: Supply.values.byName(j['supply']! as String),
    units: j['units']! as int,
    arrivesOn: GameDay(j['arrivesOn']! as int),
    size: j['size']! as int,
  );
}

/// What the player can build on the farm (the owner's decision of 13 Nov
/// 2026: the farm starts small, a pen, a 6,000 L tank and a feed shade, and
/// every other facility is bought and built in its place). Prices in riyals:
/// (field) the 30,000 L tank's from its maker (Marjan, SAR 14,110, research
/// section 7); (balance) the rest, approved by the owner. (balance) [most]
/// is how many one farm can have (the farm drawn has room for five more pens:
/// a bigger herd waits for more farms, GDD 4.1), and what each adds: head of
/// room, litres of tank, kilograms of store.
enum Facility {
  /// Another pen: room for ten more head.
  pen(price: 12000, most: 5, head: 10),

  /// A 30,000 L tank beside the first: a 19 t tanker fits it.
  tank(price: 14110, most: 1, litres: 30000),

  /// A feed store for ten tonnes.
  store(price: 18000, most: 1, kg: 10000),

  /// The shepherd's caravan: needed before a shepherd is hired.
  caravan(price: 25000, most: 1),

  /// The tent for guests and coffee (بيت الشعر).
  tent(price: 15000, most: 1),

  /// The farm's room, a sitting room with air conditioning.
  room(price: 60000, most: 1);

  const Facility({
    required this.price,
    required this.most,
    this.head = 0,
    this.litres = 0,
    this.kg = 0,
  });
  final int price;
  final int most;
  final int head;
  final int litres;
  final int kg;
}

/// A facility being built, done on [doneOn].
class Construction {
  const Construction(this.facility, this.doneOn);
  final Facility facility;
  final GameDay doneOn;

  Map<String, Object?> toJson() => {
    'facility': facility.name,
    'doneOn': doneOn.value,
  };

  static Construction fromJson(Map<String, Object?> j) => Construction(
    Facility.values.byName(j['facility']! as String),
    GameDay(j['doneOn']! as int),
  );
}

/// How much of a nursing camel's milk is left to her calf; the rest is
/// milked and sold (the owner's decision of 13 Nov 2026).
enum CalfShare {
  all(1),
  half(0.5),
  quarter(0.25);

  const CalfShare(this.part);
  final double part;
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
    this.calfShare = CalfShare.half,
    this.milkIncome = 0,
    this.milkOn,
    List<Delivery>? deliveries,
    Set<Supply>? short,
    Map<Facility, int>? built,
    List<Construction>? building,
  }) : deliveries = deliveries ?? [],
       short = short ?? {},
       built = built ?? {},
       building = building ?? [];

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

  /// The milk left to the calves.
  CalfShare calfShare;

  /// What the last day's milk brought, and the day (none yet on a new
  /// game's first day).
  int milkIncome;
  GameDay? milkOn;

  /// The facilities built beyond the first pen, tank and feed shade, and
  /// how many of each; and those being built.
  final Map<Facility, int> built;
  final List<Construction> building;

  int has(Facility f) => built[f] ?? 0;

  /// Built, or being built.
  int hasOrBuilding(Facility f) =>
      has(f) + building.where((b) => b.facility == f).length;

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
    'calfShare': calfShare.name,
    'milkIncome': milkIncome,
    'milkOn': milkOn?.value,
    'built': {
      for (final f in Facility.values)
        if (has(f) > 0) f.name: has(f),
    },
    'building': [for (final b in building) b.toJson()],
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
      for (final s in (j['short'] as List<Object?>?) ?? const [])
        Supply.values.byName(s! as String),
    },
    deliveries: [
      for (final d in j['deliveries']! as List<Object?>)
        Delivery.fromJson(d! as Map<String, Object?>),
    ],
    calfShare: CalfShare.values.byName(j['calfShare']! as String),
    milkIncome: j['milkIncome']! as int,
    milkOn: j['milkOn'] == null ? null : GameDay(j['milkOn']! as int),
    built: {
      for (final e in (j['built']! as Map<String, Object?>).entries)
        Facility.values.byName(e.key): e.value! as int,
    },
    building: [
      for (final b in j['building']! as List<Object?>)
        Construction.fromJson(b! as Map<String, Object?>),
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
  milk,

  /// A late festival registration's fee (GDD 7).
  entryFee,

  /// The secret vet's price for a treatment (GDD 7.1).
  tampering,

  /// A fine for a treatment found (GDD 7.1): at a festival (its ref the
  /// festival) or outside one, by the vet or the daily look (its ref the
  /// camel).
  fine,

  /// A fine for a treatment found by a buyer's or the broker's examination
  /// before paying (its ref the camel; the owner's decision 12).
  fineAtSale,
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
    Map<ColorCategory, double>? reputation,
    this.onAccount = 0,
  }) : ledger = ledger ?? [],
       reputation = reputation ?? {};

  final OwnerId id;
  String name;
  Riyal cash;
  final Farm farm;

  /// The colour family the player chose to specialise in (name only here;
  /// see ColorCategory).
  final String favourite;
  final List<LedgerEntry> ledger;

  /// The name the player has in each colour family (الصيت, GDD 8), 0 to
  /// 100: raised by placings, lowered when caught cheating (GDD 7.1). A
  /// family not in the map is at Balance.startingReputation.
  final Map<ColorCategory, double> reputation;

  /// Feed, water and vet treatments bought on account and not yet paid
  /// (Account): the income that comes in pays it first, and it is cleared
  /// when the money is back above zero. Never a fine.
  int onAccount;

  double reputationIn(ColorCategory c) =>
      reputation[c] ?? Balance.startingReputation;

  Map<String, Object?> toJson() => {
    'id': id.value,
    'name': name,
    'cash': cash.value,
    'farm': farm.toJson(),
    'favourite': favourite,
    'ledger': [for (final l in ledger) l.toJson()],
    'reputation': {for (final e in reputation.entries) e.key.name: e.value},
    'onAccount': onAccount,
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
    reputation: {
      for (final e in (j['reputation']! as Map<String, Object?>).entries)
        ColorCategory.values.byName(e.key): (e.value! as num).toDouble(),
    },
    onAccount: j['onAccount']! as int,
  );
}
