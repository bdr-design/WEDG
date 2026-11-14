// What the player holds of the hunting season (task T18): his falcons, his
// permits, his trapping gear and what is on its way. Kept on the player only
// once he has touched falcons (a game that never does is saved as before).
import '../catalog/falconry.dart';
import '../common/ids.dart';
import '../common/time.dart';

/// How one of his falcons came to him.
enum FalconHow { bought, trapped }

/// Where a falcon is.
enum FalconWhere {
  /// In the falcons' room (or with him on a trip).
  home,

  /// Lost on a flight, not yet found (the owner's decision 6).
  lost,
}

class Falcon {
  Falcon({
    required this.id,
    required this.name,
    required this.species,
    required this.female,
    required this.hatched,
    required this.how,
    required this.on,
    this.route,
    this.price,
    this.ground,
    required this.lengthQ,
    required this.widthQ,
    required this.weightG,
    this.passport,
    this.ring = false,
    this.trapDoc,
    required this.skill,
    this.value,
    this.dauDays = 0,
    this.caredOn,
    this.flights = 0,
    Map<Quarry, int>? taken,
    this.where = FalconWhere.home,
    this.keep = false,
    this.flownOn,
    this.flownToday = 0,
    this.lostOn,
    this.searchedOn,
    this.tracker = false,
  }) : taken = taken ?? {};

  final FalconId id;
  final String name;
  final FalconSpecies species;
  final bool female;

  /// The year it hatched (its age class: FalconAge.on).
  final int hatched;

  /// How and when it came, and from where: the route and the price it was
  /// bought at, or the ground it was trapped on.
  final FalconHow how;
  final GameDay on;
  final FalconRoute? route;
  final int? price;
  final Ground? ground;

  /// Its length and width in quarter inches and its weight in grams, as the
  /// sale pages give them [187][216] (what the width measures is not known).
  final int lengthQ;
  final int widthQ;
  final int weightG;

  /// Its passport's number (جواز الصقر: the proof of ownership [128][131]):
  /// a bought falcon's comes with it in his name; a trapped bird's once the
  /// club has checked it and documented the trapping [190][191][192].
  String? passport;

  /// The electronic ring (الحجل الإلكتروني), fitted after a sale at the
  /// trapping auction [191].
  bool ring;

  /// The trapping registration document's number (وثيقة تسجيل طرح [192]).
  String? trapDoc;

  /// HIDDEN: how good a hunter it is, 0 to 1 (never shown: the GDD 13.1,
  /// «مهارة الصقر ما تنعرض رقم أبد»).
  final double skill;

  /// HIDDEN: a trapped bird's worth at the trapping auction (never a number
  /// before the sale [187]; the design: «قيمته ما تنعرف إلا بالمزاد»).
  final int? value;

  /// Days of الدعو done (the training before its first outing), and the
  /// last day it was cared for.
  int dauDays;
  GameDay? caredOn;

  /// Its outings' flights, and what it took.
  int flights;
  final Map<Quarry, int> taken;

  FalconWhere where;

  /// A trapped bird he chose to keep: his for good, never offered for sale
  /// (the owner's decision 8 of 14 Nov 2026).
  bool keep;

  /// The last day it flew and its flights that day (TrapOdds.flightsADay).
  GameDay? flownOn;
  int flownToday;

  /// The day it was lost, and the last day he looked for it.
  GameDay? lostOn;
  GameDay? searchedOn;

  /// It wears its own tracker (fitted to it when the one ordered for it
  /// came: the answers' Q-27).
  bool tracker;

  /// Its flights today.
  int flightsOn(GameDay day) => flownOn == day ? flownToday : 0;

  FalconAge ageOn(GameDay day) => FalconAge.on(day, hatched);

  Map<String, Object?> toJson() => {
    'id': id.value,
    'name': name,
    'species': species.name,
    'female': female,
    'hatched': hatched,
    'how': how.name,
    'on': on.value,
    if (route != null) 'route': route!.name,
    'price': ?price,
    if (ground != null) 'ground': ground!.name,
    'lengthQ': lengthQ,
    'widthQ': widthQ,
    'weightG': weightG,
    'passport': ?passport,
    if (ring) 'ring': true,
    'trapDoc': ?trapDoc,
    'skill': skill,
    'value': ?value,
    'dauDays': dauDays,
    if (caredOn != null) 'caredOn': caredOn!.value,
    'flights': flights,
    if (taken.isNotEmpty)
      'taken': {for (final e in taken.entries) e.key.name: e.value},
    if (where != FalconWhere.home) 'where': where.name,
    if (keep) 'keep': true,
    if (flownOn != null) 'flownOn': flownOn!.value,
    if (flownToday != 0) 'flownToday': flownToday,
    if (lostOn != null) 'lostOn': lostOn!.value,
    if (searchedOn != null) 'searchedOn': searchedOn!.value,
    if (tracker) 'tracker': true,
  };

  static Falcon fromJson(Map<String, Object?> j) => Falcon(
    id: FalconId(j['id']! as String),
    name: j['name']! as String,
    species: FalconSpecies.values.byName(j['species']! as String),
    female: j['female']! as bool,
    hatched: j['hatched']! as int,
    how: FalconHow.values.byName(j['how']! as String),
    on: GameDay(j['on']! as int),
    route: j['route'] == null
        ? null
        : FalconRoute.values.byName(j['route']! as String),
    price: j['price'] as int?,
    ground: j['ground'] == null
        ? null
        : Ground.values.byName(j['ground']! as String),
    lengthQ: j['lengthQ']! as int,
    widthQ: j['widthQ']! as int,
    weightG: j['weightG']! as int,
    passport: j['passport'] as String?,
    ring: j['ring'] == true,
    trapDoc: j['trapDoc'] as String?,
    skill: (j['skill']! as num).toDouble(),
    value: j['value'] as int?,
    dauDays: j['dauDays']! as int,
    caredOn: j['caredOn'] == null ? null : GameDay(j['caredOn']! as int),
    flights: j['flights']! as int,
    taken: {
      for (final e
          in ((j['taken'] as Map<String, Object?>?) ?? const {}).entries)
        Quarry.values.byName(e.key): e.value! as int,
    },
    where: j['where'] == null
        ? FalconWhere.home
        : FalconWhere.values.byName(j['where']! as String),
    keep: j['keep'] == true,
    flownOn: j['flownOn'] == null ? null : GameDay(j['flownOn']! as int),
    flownToday: (j['flownToday'] as int?) ?? 0,
    lostOn: j['lostOn'] == null ? null : GameDay(j['lostOn']! as int),
    searchedOn: j['searchedOn'] == null
        ? null
        : GameDay(j['searchedOn']! as int),
    tracker: j['tracker'] == true,
  );
}

/// Gear on its way to the farm (as feed comes: Balance.deliveryDays).
class GearDelivery {
  const GearDelivery(this.gear, this.units, this.arrivesOn, {this.falcon});
  final Gear gear;
  final int units;
  final GameDay arrivesOn;

  /// The falcon a tracker is for (fitted to it on arrival).
  final FalconId? falcon;

  Map<String, Object?> toJson() => {
    'gear': gear.name,
    'units': units,
    'arrivesOn': arrivesOn.value,
    if (falcon != null) 'falcon': falcon!.value,
  };

  static GearDelivery fromJson(Map<String, Object?> j) => GearDelivery(
    Gear.values.byName(j['gear']! as String),
    j['units']! as int,
    GameDay(j['arrivesOn']! as int),
    falcon: j['falcon'] == null ? null : FalconId(j['falcon']! as String),
  );
}

/// A stretch away for falcons (the trip of days with a camp, or a day's
/// outing to a near ground): the drive out, the days at the ground, the
/// drive home; the farm runs as on any day meanwhile.
class Trip {
  Trip({
    required this.kind,
    required this.ground,
    required this.startedOn,
    required this.endOn,
    required this.oneDay,
    required this.arriveOn,
    required this.arriveMinute,
    this.homeOn,
    this.homeMinute,
    this.caught = 0,
    this.released = 0,
    this.stooped = 0,
    this.flights = 0,
    this.taken = 0,
    this.suppliesUsed = 0,
  });

  final TripKind kind;

  /// Where the camp is (the mobile tent moves it: MoveCamp).
  Ground ground;
  final GameDay startedOn;

  /// The day he chose to be back by (a stop of the away call).
  final GameDay endOn;
  final bool oneDay;

  /// When the drive out reaches the ground (its working hour), and, once
  /// he has broken camp, when the drive home reaches the farm.
  GameDay arriveOn;
  int arriveMinute;
  GameDay? homeOn;
  int? homeMinute;

  bool get returning => homeOn != null;

  /// At the ground on [day] at [minute]: arrived, and not on the way home.
  bool there(GameDay day, int minute) =>
      !returning &&
      (day > arriveOn || (day == arriveOn && minute >= arriveMinute));

  /// Home by [day] at [minute].
  bool home(GameDay day, int minute) =>
      returning && (day > homeOn! || (day == homeOn && minute >= homeMinute!));

  /// The trip's own lines for the summary.
  int caught;
  int released;
  int stooped;
  int flights;
  int taken;
  int suppliesUsed;

  Map<String, Object?> toJson() => {
    'kind': kind.name,
    'ground': ground.name,
    'startedOn': startedOn.value,
    'endOn': endOn.value,
    'oneDay': oneDay,
    'arriveOn': arriveOn.value,
    'arriveMinute': arriveMinute,
    if (homeOn != null) 'homeOn': homeOn!.value,
    'homeMinute': ?homeMinute,
    'caught': caught,
    'released': released,
    'stooped': stooped,
    'flights': flights,
    'taken': taken,
    'suppliesUsed': suppliesUsed,
  };

  static Trip fromJson(Map<String, Object?> j) => Trip(
    kind: TripKind.values.byName(j['kind']! as String),
    ground: Ground.values.byName(j['ground']! as String),
    startedOn: GameDay(j['startedOn']! as int),
    endOn: GameDay(j['endOn']! as int),
    oneDay: j['oneDay']! as bool,
    arriveOn: GameDay(j['arriveOn']! as int),
    arriveMinute: j['arriveMinute']! as int,
    homeOn: j['homeOn'] == null ? null : GameDay(j['homeOn']! as int),
    homeMinute: j['homeMinute'] as int?,
    caught: j['caught']! as int,
    released: j['released']! as int,
    stooped: j['stooped']! as int,
    flights: j['flights']! as int,
    taken: j['taken']! as int,
    suppliesUsed: j['suppliesUsed']! as int,
  );
}

/// A day's trapping, kept on the player by the day (never on a trip: a camp
/// broken and made again finds the same day): the one ground he works that
/// day, the falcon he has seen, the lures tried at it, whether it is done
/// with, the windows he has looked in.
class DayWork {
  DayWork({
    required this.day,
    required this.ground,
    this.sighted = false,
    this.tries = 0,
    this.resolved = false,
    Set<TrapWindow>? looked,
    Map<Lure, int>? lures,
  }) : looked = looked ?? {},
       lures = lures ?? {};

  final GameDay day;
  final Ground ground;
  bool sighted;
  int tries;
  bool resolved;
  final Set<TrapWindow> looked;
  final Map<Lure, int> lures;

  Map<String, Object?> toJson() => {
    'day': day.value,
    'ground': ground.name,
    'sighted': sighted,
    'tries': tries,
    'resolved': resolved,
    'looked': [
      for (final w in TrapWindow.values)
        if (looked.contains(w)) w.name,
    ],
    'lures': {for (final e in lures.entries) e.key.name: e.value},
  };

  static DayWork fromJson(Map<String, Object?> j) => DayWork(
    day: GameDay(j['day']! as int),
    ground: Ground.values.byName(j['ground']! as String),
    sighted: j['sighted']! as bool,
    tries: j['tries']! as int,
    resolved: j['resolved']! as bool,
    looked: {
      for (final w in j['looked']! as List<Object?>)
        TrapWindow.values.byName(w! as String),
    },
    lures: {
      for (final e in (j['lures']! as Map<String, Object?>).entries)
        Lure.values.byName(e.key): e.value! as int,
    },
  );
}

/// The player's part of the hunting season.
class Falconry {
  Falconry({
    List<Falcon>? falcons,
    Map<PermitKind, int>? permits,
    Map<Gear, int>? gear,
    List<GearDelivery>? coming,
    Set<String>? lotsGone,
    this.named = 0,
    List<Falcon>? held,
    Set<FalconId>? entered,
    this.trip,
    this.work,
  }) : falcons = falcons ?? [],
       held = held ?? [],
       entered = entered ?? {},
       permits = permits ?? {},
       gear = gear ?? {},
       coming = coming ?? [],
       lotsGone = lotsGone ?? {};

  /// His falcons, in the order they came.
  final List<Falcon> falcons;

  /// Each permit he holds, by the season it is for (the year its autumn
  /// falls in).
  final Map<PermitKind, int> permits;

  /// The gear in hand (pigeons by the bird, supplies by the day).
  final Map<Gear, int> gear;
  final List<GearDelivery> coming;

  /// The auctions' lots sold (to him or to another) in the season, by their
  /// keys (FalconLot.key): a lot is sold once.
  final Set<String> lotsGone;

  /// How many falcons have been named (the next name in the list).
  int named;

  /// Trapped birds that may be sold, in the hood at camp or at the farm,
  /// outside the room until sold or kept (the owner's word on Q-13/15); and
  /// those entered for tonight's trapping auction.
  final List<Falcon> held;
  final Set<FalconId> entered;

  /// The trip or the day's outing he is on, or null at home.
  Trip? trip;

  /// The last day's trapping (DayWork).
  DayWork? work;

  /// One of his birds, in the room or held for sale.
  Falcon? any(FalconId id) =>
      falcon(id) ?? held.where((f) => f.id == id).firstOrNull;

  int has(Gear g) => gear[g] ?? 0;
  int onTheWay(Gear g) =>
      coming.where((d) => d.gear == g).fold(0, (n, d) => n + d.units);

  /// [kind] held for the season open on [day].
  bool holds(PermitKind kind, GameDay day) {
    final s = kind.seasonOn(day);
    return s != null && permits[kind] == s;
  }

  Falcon? falcon(FalconId id) => falcons.where((f) => f.id == id).firstOrNull;

  Map<String, Object?> toJson() => {
    'falcons': [for (final f in falcons) f.toJson()],
    'permits': {for (final e in permits.entries) e.key.name: e.value},
    'gear': {
      for (final g in Gear.values)
        if (has(g) > 0) g.name: has(g),
    },
    'coming': [for (final d in coming) d.toJson()],
    'lotsGone': [...lotsGone],
    'named': named,
    if (held.isNotEmpty) 'held': [for (final f in held) f.toJson()],
    if (entered.isNotEmpty) 'entered': [for (final f in entered) f.value],
    if (trip != null) 'trip': trip!.toJson(),
    if (work != null) 'work': work!.toJson(),
  };

  static Falconry fromJson(Map<String, Object?> j) => Falconry(
    falcons: [
      for (final f in j['falcons']! as List<Object?>)
        Falcon.fromJson(f! as Map<String, Object?>),
    ],
    permits: {
      for (final e in (j['permits']! as Map<String, Object?>).entries)
        PermitKind.values.byName(e.key): e.value! as int,
    },
    gear: {
      for (final e in (j['gear']! as Map<String, Object?>).entries)
        Gear.values.byName(e.key): e.value! as int,
    },
    coming: [
      for (final d in j['coming']! as List<Object?>)
        GearDelivery.fromJson(d! as Map<String, Object?>),
    ],
    lotsGone: {for (final k in j['lotsGone']! as List<Object?>) k! as String},
    named: j['named']! as int,
    held: [
      for (final f in (j['held'] as List<Object?>?) ?? const [])
        Falcon.fromJson(f! as Map<String, Object?>),
    ],
    entered: {
      for (final f in (j['entered'] as List<Object?>?) ?? const [])
        FalconId(f! as String),
    },
    trip: j['trip'] == null
        ? null
        : Trip.fromJson(j['trip']! as Map<String, Object?>),
    work: j['work'] == null
        ? null
        : DayWork.fromJson(j['work']! as Map<String, Object?>),
  );
}
