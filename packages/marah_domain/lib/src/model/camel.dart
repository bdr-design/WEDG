import '../catalog/catalog.dart';
import '../common/ids.dart';
import '../common/time.dart';

/// Where a camel is in its life. Records are never deleted: sold and dead
/// camels stay in the registry so pedigrees, offspring records and history
/// keep working.
enum CamelStatus { alive, dead, gone }

enum HealthStatus { healthy, sick, treated }

/// Parent reference kept on the calf. [id] may point at a camel that is not
/// in this world's registry (an outside sire or dam).
class ParentRef {
  const ParentRef({
    required this.id,
    required this.name,
    required this.category,
  });

  final CamelId id;
  final String name;
  final ColorCategory category;

  Map<String, Object?> toJson() => {
    'id': id.value,
    'name': name,
    'cat': category.name,
  };

  static ParentRef fromJson(Map<String, Object?> j) => ParentRef(
    id: CamelId(j['id']! as String),
    name: j['name']! as String,
    category: ColorCategory.values.byName(j['cat']! as String),
  );
}

/// A mating and its outcome. The sire's breeding values are copied here so
/// the calf can be bred even if the bull belongs to someone else or is sold.
class Pregnancy {
  Pregnancy({
    required this.sire,
    required this.sireGenes,
    required this.matedOn,
    required this.checkOn,
    required this.dueOn,
    required this.conceived,
    this.confirmed = false,
  });

  final ParentRef sire;
  final Map<Trait, double> sireGenes;
  final GameDay matedOn;

  /// When the pregnancy check reveals the result.
  final GameDay checkOn;
  final GameDay dueOn;

  /// Decided at mating, hidden from the owner until [checkOn].
  final bool conceived;
  bool confirmed;

  Map<String, Object?> toJson() => {
    'sire': sire.toJson(),
    'sireGenes': traitsToJson(sireGenes),
    'matedOn': matedOn.value,
    'checkOn': checkOn.value,
    'dueOn': dueOn.value,
    'conceived': conceived,
    'confirmed': confirmed,
  };

  static Pregnancy fromJson(Map<String, Object?> j) => Pregnancy(
    sire: ParentRef.fromJson(j['sire']! as Map<String, Object?>),
    sireGenes: traitsFromJson(j['sireGenes']! as List<Object?>),
    matedOn: GameDay(j['matedOn']! as int),
    checkOn: GameDay(j['checkOn']! as int),
    dueOn: GameDay(j['dueOn']! as int),
    conceived: j['conceived']! as bool,
    confirmed: j['confirmed']! as bool,
  );
}

/// A contest placing on the camel's record.
class Placing {
  const Placing({
    required this.festivalId,
    required this.festivalName,
    required this.roundId,
    required this.rank,
    required this.of,
    required this.day,
    required this.tier,
    required this.prize,
  });

  final FestivalId festivalId;
  final String festivalName;
  final RoundId roundId;
  final int rank;
  final int of;
  final GameDay day;

  /// 1 local, 2 regional, 3 grand.
  final int tier;
  final int prize;

  Map<String, Object?> toJson() => {
    'festival': festivalId.value,
    'festivalName': festivalName,
    'round': roundId.value,
    'rank': rank,
    'of': of,
    'day': day.value,
    'tier': tier,
    'prize': prize,
  };

  static Placing fromJson(Map<String, Object?> j) => Placing(
    festivalId: FestivalId(j['festival']! as String),
    festivalName: j['festivalName']! as String,
    roundId: RoundId(j['round']! as String),
    rank: j['rank']! as int,
    of: j['of']! as int,
    day: GameDay(j['day']! as int),
    tier: j['tier']! as int,
    prize: j['prize']! as int,
  );
}

/// A camel in the world registry.
///
/// [genes] and [env] are hidden information: what the camel passes on and
/// its permanent non-genetic deviation. Clients only ever see what the body
/// shows (see views), never these numbers.
class Camel {
  Camel({
    required this.id,
    required this.name,
    required this.sex,
    required this.category,
    required this.born,
    required this.ownerId,
    required this.chip,
    required this.genes,
    required this.env,
    required this.condition,
    required this.acquiredOn,
    this.status = CamelStatus.alive,
    this.endedOn,
    this.health = HealthStatus.healthy,
    this.illness,
    this.sickSince,
    this.recoversOn,
    this.pregnancy,
    this.lastCalvedOn,
    this.calvings = 0,
    this.lastServiceOn,
    this.sire,
    this.dam,
    this.crossbred = false,
    this.purchasePrice = 0,
    this.lastPlayerOwner,
    this.bannedThrough,
    List<Placing>? placings,
  }) : placings = placings ?? [];

  final CamelId id;
  String name;
  final Sex sex;
  final ColorCategory category;
  final GameDay born;
  OwnerId ownerId;

  /// Microchip (الشريحة), required for contests.
  final String chip;
  final Map<Trait, double> genes;
  final Map<Trait, double> env;

  /// Body condition 0–100.
  double condition;
  GameDay acquiredOn;
  CamelStatus status;

  /// When the camel died or left the world.
  GameDay? endedOn;

  HealthStatus health;
  Illness? illness;
  GameDay? sickSince;
  GameDay? recoversOn;

  Pregnancy? pregnancy;
  GameDay? lastCalvedOn;
  int calvings;
  GameDay? lastServiceOn;

  final ParentRef? sire;
  final ParentRef? dam;
  final bool crossbred;
  int purchasePrice;

  /// The last player who owned this camel. Set when a player buys or
  /// breeds it and kept after it is sold, so its record is never dropped.
  OwnerId? lastPlayerOwner;

  /// Barred from festivals through this season (the year its autumn falls
  /// in), kept when the camel is sold on: a treatment found on it or on a
  /// camel of its owner's (GDD 7.1; research section 3, [102]).
  int? bannedThrough;

  /// Everything that can change after the camel is created, in a fixed
  /// order. The store compares this with what it last wrote and rewrites
  /// the row only when something differs (exact, no hashing).
  List<Object?> mutableFields() => [
    name,
    ownerId.value,
    condition,
    acquiredOn.value,
    status.index,
    endedOn?.value,
    health.index,
    illness?.index,
    sickSince?.value,
    recoversOn?.value,
    pregnancy?.sire.id.value,
    pregnancy?.matedOn.value,
    pregnancy?.checkOn.value,
    pregnancy?.dueOn.value,
    pregnancy?.conceived,
    pregnancy?.confirmed,
    lastCalvedOn?.value,
    calvings,
    lastServiceOn?.value,
    purchasePrice,
    placings.length,
    lastPlayerOwner?.value,
    bannedThrough,
  ];
  final List<Placing> placings;

  bool get isAlive => status == CamelStatus.alive;
  int ageDays(GameDay today) => today.daysSince(born);
  int ageYears(GameDay today) => ageDays(today) ~/ 365;
  AgeClass ageClass(GameDay today) => AgeClass.fromDays(ageDays(today));
  bool get pregnancyConfirmed => pregnancy?.confirmed ?? false;

  /// Home-bred: born while already owned by its owner.
  bool get homeBred => acquiredOn == born;

  ParentRef get asParent => ParentRef(id: id, name: name, category: category);

  Map<String, Object?> toJson() => {
    'id': id.value,
    'name': name,
    'sex': sex.name,
    'cat': category.name,
    'born': born.value,
    'owner': ownerId.value,
    'chip': chip,
    'genes': traitsToJson(genes),
    'env': traitsToJson(env),
    'condition': condition,
    'acquiredOn': acquiredOn.value,
    'status': status.name,
    'endedOn': endedOn?.value,
    'health': health.name,
    'illness': illness?.name,
    'sickSince': sickSince?.value,
    'recoversOn': recoversOn?.value,
    'pregnancy': pregnancy?.toJson(),
    'lastCalvedOn': lastCalvedOn?.value,
    'calvings': calvings,
    'lastServiceOn': lastServiceOn?.value,
    'sire': sire?.toJson(),
    'dam': dam?.toJson(),
    'crossbred': crossbred,
    'purchasePrice': purchasePrice,
    'lastPlayerOwner': lastPlayerOwner?.value,
    if (bannedThrough != null) 'bannedThrough': bannedThrough,
    'placings': [for (final p in placings) p.toJson()],
  };

  static Camel fromJson(Map<String, Object?> j) {
    GameDay? day(String k) => j[k] == null ? null : GameDay(j[k]! as int);
    return Camel(
      id: CamelId(j['id']! as String),
      name: j['name']! as String,
      sex: Sex.values.byName(j['sex']! as String),
      category: ColorCategory.values.byName(j['cat']! as String),
      born: GameDay(j['born']! as int),
      ownerId: OwnerId(j['owner']! as String),
      chip: j['chip']! as String,
      genes: traitsFromJson(j['genes']! as List<Object?>),
      env: traitsFromJson(j['env']! as List<Object?>),
      condition: (j['condition']! as num).toDouble(),
      acquiredOn: GameDay(j['acquiredOn']! as int),
      status: CamelStatus.values.byName(j['status']! as String),
      endedOn: day('endedOn'),
      health: HealthStatus.values.byName(j['health']! as String),
      illness: j['illness'] == null
          ? null
          : Illness.values.byName(j['illness']! as String),
      sickSince: day('sickSince'),
      recoversOn: day('recoversOn'),
      pregnancy: j['pregnancy'] == null
          ? null
          : Pregnancy.fromJson(j['pregnancy']! as Map<String, Object?>),
      lastCalvedOn: day('lastCalvedOn'),
      calvings: j['calvings']! as int,
      lastServiceOn: day('lastServiceOn'),
      sire: j['sire'] == null
          ? null
          : ParentRef.fromJson(j['sire']! as Map<String, Object?>),
      dam: j['dam'] == null
          ? null
          : ParentRef.fromJson(j['dam']! as Map<String, Object?>),
      crossbred: j['crossbred']! as bool,
      purchasePrice: j['purchasePrice']! as int,
      lastPlayerOwner: j['lastPlayerOwner'] == null
          ? null
          : OwnerId(j['lastPlayerOwner']! as String),
      bannedThrough: j['bannedThrough'] as int?,
      placings: [
        for (final p in j['placings']! as List<Object?>)
          Placing.fromJson(p! as Map<String, Object?>),
      ],
    );
  }
}

/// Traits are written as a list in [Trait] order. Values are kept at 2
/// decimals in memory (see q2), so the round trip is exact and compact.
List<double> traitsToJson(Map<Trait, double> m) => [
  for (final t in Trait.values) m[t]!,
];

Map<Trait, double> traitsFromJson(List<Object?> j) => {
  for (final t in Trait.values) t: (j[t.index]! as num).toDouble(),
};
