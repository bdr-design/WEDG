// The hunting season's events (task T18). Like every event they carry no
// display text: the Arabic is the catalog's (FalconLines) and the phone's.
part of 'events.dart';

DomainEvent? _huntEvent(
  String type,
  GameDay day,
  OwnerId? owner,
  CamelId? camel,
  Map<String, Object?> j,
) => switch (type) {
  'permitBought' => PermitBought(
    day,
    owner: owner,
    kind: PermitKind.values.byName(j['kind']! as String),
    season: j['season']! as int,
    fee: j['fee']! as int,
  ),
  'gearOrdered' => GearOrdered(
    day,
    owner: owner,
    gear: Gear.values.byName(j['gear']! as String),
    units: j['units']! as int,
    cost: j['cost']! as int,
    arrivesOn: GameDay(j['arrivesOn']! as int),
  ),
  'gearDelivered' => GearDelivered(
    day,
    owner: owner,
    gear: Gear.values.byName(j['gear']! as String),
    units: j['units']! as int,
  ),
  'falconBought' => FalconBought(
    day,
    owner: owner,
    falcon: j['falcon']! as String,
    name: j['name']! as String,
    species: FalconSpecies.values.byName(j['species']! as String),
    route: FalconRoute.values.byName(j['route']! as String),
    price: j['price']! as int,
  ),
  'falconLotLost' => FalconLotLost(
    day,
    owner: owner,
    lot: j['lot']! as String,
    route: FalconRoute.values.byName(j['route']! as String),
    price: j['price']! as int,
  ),
  'tripChanged' => TripChanged(
    day,
    owner: owner,
    what: TripChange.values.byName(j['what']! as String),
    kind: TripKind.values.byName(j['kind']! as String),
    ground: Ground.values.byName(j['ground']! as String),
    lines: (j['lines']! as Map<String, Object?>).cast<String, int>(),
  ),
  'trapResult' => TrapResult(
    day,
    owner: owner,
    outcome: TrapOutcome.values.byName(j['outcome']! as String),
    window: j['window'] == null
        ? null
        : TrapWindow.values.byName(j['window']! as String),
    species: j['species'] == null
        ? null
        : FalconSpecies.values.byName(j['species']! as String),
    farkh: j['farkh'] as bool?,
    falcon: j['falcon'] as String?,
  ),
  'castResult' => CastResult(
    day,
    owner: owner,
    falcon: j['falcon']! as String,
    name: j['name']! as String,
    outcome: CastOutcome.values.byName(j['outcome']! as String),
    quarry: j['quarry'] == null
        ? null
        : Quarry.values.byName(j['quarry']! as String),
  ),
  'falconFate' => FalconFate(
    day,
    owner: owner,
    falcon: j['falcon']! as String,
    name: j['name']! as String,
    fate: Fate.values.byName(j['fate']! as String),
    price: j['price'] as int?,
  ),
  _ => null,
};

/// A permit bought for [season] (the year its autumn falls in).
final class PermitBought extends DomainEvent {
  const PermitBought(
    super.day, {
    super.owner,
    required this.kind,
    required this.season,
    required this.fee,
  });
  final PermitKind kind;
  final int season;
  final int fee;
  @override
  String get type => 'permitBought';
  @override
  Map<String, Object?> fieldsToJson() => {
    'kind': kind.name,
    'season': season,
    'fee': fee,
  };
}

/// Gear ordered from the club's app, on its way.
final class GearOrdered extends DomainEvent {
  const GearOrdered(
    super.day, {
    super.owner,
    required this.gear,
    required this.units,
    required this.cost,
    required this.arrivesOn,
  });
  final Gear gear;
  final int units;
  final int cost;
  final GameDay arrivesOn;
  @override
  String get type => 'gearOrdered';
  @override
  Map<String, Object?> fieldsToJson() => {
    'gear': gear.name,
    'units': units,
    'cost': cost,
    'arrivesOn': arrivesOn.value,
  };
}

/// Gear arrived at the farm.
final class GearDelivered extends DomainEvent {
  const GearDelivered(
    super.day, {
    super.owner,
    required this.gear,
    required this.units,
  });
  final Gear gear;
  final int units;
  @override
  String get type => 'gearDelivered';
  @override
  Map<String, Object?> fieldsToJson() => {'gear': gear.name, 'units': units};
}

/// A falcon bought at [route] for [price]: in the falcons' room, its
/// passport in his name.
final class FalconBought extends DomainEvent {
  const FalconBought(
    super.day, {
    super.owner,
    required this.falcon,
    required this.name,
    required this.species,
    required this.route,
    required this.price,
  });
  final String falcon;
  final String name;
  final FalconSpecies species;
  final FalconRoute route;
  final int price;
  @override
  String get type => 'falconBought';
  @override
  Map<String, Object?> fieldsToJson() => {
    'falcon': falcon,
    'name': name,
    'species': species.name,
    'route': route.name,
    'price': price,
  };
}

/// His ceiling did not reach the hammer: the lot went to another bidder at
/// [price], told as an auction tells it, and is gone for good.
final class FalconLotLost extends DomainEvent {
  const FalconLotLost(
    super.day, {
    super.owner,
    required this.lot,
    required this.route,
    required this.price,
  });
  final String lot;
  final FalconRoute route;
  final int price;
  @override
  String get type => 'falconLotLost';
  @override
  Map<String, Object?> fieldsToJson() => {
    'lot': lot,
    'route': route.name,
    'price': price,
  };
}

enum TripChange { started, homeward, ended, moved }

/// A trip started, ended (with its lines for the summary: days, caught,
/// released, stooped, flights, taken, supplies used) or its camp moved.
final class TripChanged extends DomainEvent {
  const TripChanged(
    super.day, {
    super.owner,
    required this.what,
    required this.kind,
    required this.ground,
    this.lines = const {},
  });
  final TripChange what;
  final TripKind kind;
  final Ground ground;
  final Map<String, int> lines;
  @override
  String get type => 'tripChanged';
  @override
  Map<String, Object?> fieldsToJson() => {
    'what': what.name,
    'kind': kind.name,
    'ground': ground.name,
    'lines': lines,
  };
}

/// What the trapping answered.
enum TrapOutcome {
  /// A falcon seen ([window]).
  inSight,

  /// Nothing in sight.
  nothingInSight,

  /// A lure released with no falcon seen: nothing came.
  nothingCame,

  /// The falcon would not take the lure (it is still there, unless it has
  /// refused [TrapOdds.triesMost] times: then it went).
  refused,
  refusedAndWent,

  /// It stooped and was not held.
  stooped,

  /// In the net: a sellable bird ([falcon]: held for sale).
  netted,

  /// In the net and released at once ([species], [farkh]: the line is
  /// FalconLines.release).
  released,
}

final class TrapResult extends DomainEvent {
  const TrapResult(
    super.day, {
    super.owner,
    required this.outcome,
    this.window,
    this.species,
    this.farkh,
    this.falcon,
  });
  final TrapOutcome outcome;
  final TrapWindow? window;
  final FalconSpecies? species;
  final bool? farkh;
  final String? falcon;
  @override
  String get type => 'trapResult';
  @override
  Map<String, Object?> fieldsToJson() => {
    'outcome': outcome.name,
    if (window != null) 'window': window!.name,
    if (species != null) 'species': species!.name,
    'farkh': ?farkh,
    'falcon': ?falcon,
  };
}

enum CastOutcome { caught, missed, lost }

/// A cast: the quarry taken, missed, or the falcon did not come back.
final class CastResult extends DomainEvent {
  const CastResult(
    super.day, {
    super.owner,
    required this.falcon,
    required this.name,
    required this.outcome,
    this.quarry,
  });
  final String falcon;
  final String name;
  final CastOutcome outcome;
  final Quarry? quarry;
  @override
  String get type => 'castResult';
  @override
  Map<String, Object?> fieldsToJson() => {
    'falcon': falcon,
    'name': name,
    'outcome': outcome.name,
    if (quarry != null) 'quarry': quarry!.name,
  };
}

/// What became of one of his birds.
enum Fate {
  /// Entered for tonight's trapping auction; then sold ([price] in full).
  entered,
  sold,

  /// Kept as his own (in the room, registered, its passport).
  kept,

  /// Set free by him (a kept peregrine, from February).
  freed,

  /// Neither sold nor kept when the trapping auction closed: set free.
  freedAtClose,

  /// A lost falcon found, not found today, or gone for good.
  found,
  notFound,
  gone,

  /// Left without الدعو two weeks: it stepped back a week.
  steppedBack,

  /// الدعو done today.
  cared,
}

final class FalconFate extends DomainEvent {
  const FalconFate(
    super.day, {
    super.owner,
    required this.falcon,
    required this.name,
    required this.fate,
    this.price,
  });
  final String falcon;
  final String name;
  final Fate fate;
  final int? price;
  @override
  String get type => 'falconFate';
  @override
  Map<String, Object?> fieldsToJson() => {
    'falcon': falcon,
    'name': name,
    'fate': fate.name,
    'price': ?price,
  };
}
