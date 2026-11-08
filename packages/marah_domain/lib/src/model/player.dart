import '../catalog/region.dart';
import '../common/ids.dart';
import '../common/money.dart';
import '../common/time.dart';

/// Feeding programme for the herd (game balance on real rations).
enum FeedPlan {
  economy(costFactor: 0.75, conditionTarget: 58),
  standard(costFactor: 1.0, conditionTarget: 74),
  premium(costFactor: 1.55, conditionTarget: 90);

  const FeedPlan({required this.costFactor, required this.conditionTarget});
  final double costFactor;
  final int conditionTarget;
}

/// The player's farm (العزبة).
class Farm {
  Farm({
    required this.name,
    required this.region,
    required this.capacity,
    required this.shepherds,
    required this.feedPlan,
  });

  String name;
  Region region;
  int capacity;
  int shepherds;
  FeedPlan feedPlan;

  Map<String, Object?> toJson() => {
    'name': name,
    'region': region.name,
    'capacity': capacity,
    'shepherds': shepherds,
    'feedPlan': feedPlan.name,
  };

  static Farm fromJson(Map<String, Object?> j) => Farm(
    name: j['name']! as String,
    region: Region.values.byName(j['region']! as String),
    capacity: j['capacity']! as int,
    shepherds: j['shepherds']! as int,
    feedPlan: FeedPlan.values.byName(j['feedPlan']! as String),
  );
}

enum LedgerCategory {
  opening,
  purchase,
  sale,
  feed,
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
