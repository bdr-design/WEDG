import '../common/ids.dart';
import '../common/time.dart';
import '../events.dart';
import 'camel.dart';
import 'contest.dart';
import 'market.dart';
import 'player.dart';

/// The shared world: other owners, the camel registry, markets, studs and
/// the contest calendar. Online this lives on the server.
class WorldState {
  WorldState({
    required this.seed,
    required this.day,
    required this.ids,
    required this.owners,
    required this.camels,
    required this.listings,
    required this.offers,
    required this.studs,
    required this.festivals,
    required this.plannedUntil,
  });

  /// Seed for every keyed random stream in this world.
  final int seed;

  /// The last day that has been simulated.
  GameDay day;
  final IdGenerator ids;
  final Map<OwnerId, Owner> owners;

  /// Every camel ever known to this world, alive or not.
  final Map<CamelId, Camel> camels;
  final Map<ListingId, Listing> listings;
  final Map<OfferId, Offer> offers;
  final Map<StudId, StudOffer> studs;
  final Map<FestivalId, Festival> festivals;

  /// Contest seasons are planned up to this day.
  GameDay plannedUntil;

  Iterable<Camel> aliveOwnedBy(OwnerId owner) =>
      camels.values.where((c) => c.isAlive && c.ownerId == owner);

  Map<String, Object?> toJson() => {
    'seed': seed,
    'day': day.value,
    'idCounter': ids.counter,
    'owners': [for (final o in owners.values) o.toJson()],
    'camels': [for (final c in camels.values) c.toJson()],
    'listings': [for (final l in listings.values) l.toJson()],
    'offers': [for (final o in offers.values) o.toJson()],
    'studs': [for (final s in studs.values) s.toJson()],
    'festivals': [for (final f in festivals.values) f.toJson()],
    'plannedUntil': plannedUntil.value,
  };

  static WorldState fromJson(Map<String, Object?> j) {
    final seed = j['seed']! as int;
    List<Map<String, Object?>> list(String k) => [
      for (final e in j[k]! as List<Object?>) e! as Map<String, Object?>,
    ];
    return WorldState(
      seed: seed,
      day: GameDay(j['day']! as int),
      ids: IdGenerator(worldSeed: seed, counter: j['idCounter']! as int),
      owners: {for (final o in list('owners').map(Owner.fromJson)) o.id: o},
      camels: {for (final c in list('camels').map(Camel.fromJson)) c.id: c},
      listings: {
        for (final l in list('listings').map(Listing.fromJson)) l.id: l,
      },
      offers: {for (final o in list('offers').map(Offer.fromJson)) o.id: o},
      studs: {for (final s in list('studs').map(StudOffer.fromJson)) s.id: s},
      festivals: {
        for (final f in list('festivals').map(Festival.fromJson)) f.id: f,
      },
      plannedUntil: GameDay(j['plannedUntil']! as int),
    );
  }
}

/// A whole game: the world plus the players in it. Offline there is one
/// human player; the shape already allows many.
class GameState {
  GameState({
    required this.world,
    required this.players,
    required this.startedOn,
    required this.startedAtUtcMs,
    this.clockShiftMs = 0,
    this.lastSeenUtcMs,
    Map<String, List<DomainEvent>>? inboxes,
  }) : inboxes = inboxes ?? {};

  /// How many past events each inbox keeps. New events are always returned
  /// to the caller; this only bounds the stored history.
  static const inboxLimit = 400;

  /// Inbox key for world news that belongs to no one.
  static const publicInbox = '';

  final WorldState world;
  final Map<OwnerId, PlayerState> players;
  final GameDay startedOn;

  /// Real time (UTC, ms since epoch) when the game started. With
  /// [startedOn] it anchors the offline real-time clock (ADR 0001).
  final int startedAtUtcMs;

  /// Real time added to the clock anchor (ms). When the device clock jumps
  /// back, or an absence longer than the catch-up limit is skipped, the
  /// anchor moves so the world continues from where it is.
  int clockShiftMs;

  /// Last real time (UTC ms) the game was brought up to date.
  int? lastSeenUtcMs;

  /// Each player's news (keyed by owner id), plus public world news.
  final Map<String, List<DomainEvent>> inboxes;

  List<DomainEvent> inboxOf(OwnerId owner) => inboxes[owner.value] ?? const [];
  List<DomainEvent> get publicNews => inboxes[publicInbox] ?? const [];

  /// The offline clock for this game: one real day is one game week.
  RealTimeClock clock({DateTime Function()? now}) => RealTimeClock(
    anchorReal: DateTime.fromMillisecondsSinceEpoch(
      startedAtUtcMs + clockShiftMs,
      isUtc: true,
    ),
    anchorDay: startedOn,
    now: now,
  );

  void record(Iterable<DomainEvent> events) {
    for (final e in events) {
      final box = inboxes.putIfAbsent(e.owner?.value ?? publicInbox, () => []);
      box.add(e);
      if (box.length > inboxLimit) box.removeRange(0, box.length - inboxLimit);
    }
  }

  Map<String, Object?> toJson() => {
    'startedOn': startedOn.value,
    'startedAtUtcMs': startedAtUtcMs,
    'clockShiftMs': clockShiftMs,
    'lastSeenUtcMs': lastSeenUtcMs,
    'world': world.toJson(),
    'players': [for (final p in players.values) p.toJson()],
    'inboxes': {
      for (final e in inboxes.entries)
        e.key: [for (final ev in e.value) ev.toJson()],
    },
  };

  static GameState fromJson(Map<String, Object?> j) => GameState(
    startedOn: GameDay(j['startedOn']! as int),
    startedAtUtcMs: j['startedAtUtcMs']! as int,
    clockShiftMs: (j['clockShiftMs'] as int?) ?? 0,
    lastSeenUtcMs: j['lastSeenUtcMs'] as int?,
    world: WorldState.fromJson(j['world']! as Map<String, Object?>),
    players: {
      for (final p in (j['players']! as List<Object?>).map(
        (e) => PlayerState.fromJson(e! as Map<String, Object?>),
      ))
        p.id: p,
    },
    inboxes: {
      for (final e in (j['inboxes']! as Map<String, Object?>).entries)
        e.key: [
          for (final ev in e.value! as List<Object?>)
            DomainEvent.fromJson(ev! as Map<String, Object?>),
        ],
    },
  );
}
