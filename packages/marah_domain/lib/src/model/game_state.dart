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
    this.actionSeq = 0,
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

  /// Counts commands applied, so each command draws its own random stream.
  int actionSeq;

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
    'actionSeq': actionSeq,
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
      actionSeq: j['actionSeq']! as int,
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
    List<DomainEvent>? journal,
  }) : journal = journal ?? [];

  /// How many past events the activity log keeps. New events are always
  /// returned to the caller; this only bounds the stored history.
  static const journalLimit = 400;

  final WorldState world;
  final Map<OwnerId, PlayerState> players;
  final GameDay startedOn;

  /// Real time (UTC, ms since epoch) when the game started. With
  /// [startedOn] it anchors the offline real-time clock (ADR 0001).
  final int startedAtUtcMs;
  final List<DomainEvent> journal;

  /// The offline clock for this game: one real day is one game week.
  RealTimeClock clock({DateTime Function()? now}) => RealTimeClock(
    anchorReal: DateTime.fromMillisecondsSinceEpoch(
      startedAtUtcMs,
      isUtc: true,
    ),
    anchorDay: startedOn,
    now: now,
  );

  void record(Iterable<DomainEvent> events) {
    journal.addAll(events);
    if (journal.length > journalLimit) {
      journal.removeRange(0, journal.length - journalLimit);
    }
  }

  Map<String, Object?> toJson() => {
    'startedOn': startedOn.value,
    'startedAtUtcMs': startedAtUtcMs,
    'world': world.toJson(),
    'players': [for (final p in players.values) p.toJson()],
    'journal': [for (final e in journal) e.toJson()],
  };

  static GameState fromJson(Map<String, Object?> j) => GameState(
    startedOn: GameDay(j['startedOn']! as int),
    startedAtUtcMs: j['startedAtUtcMs']! as int,
    world: WorldState.fromJson(j['world']! as Map<String, Object?>),
    players: {
      for (final p in (j['players']! as List<Object?>).map(
        (e) => PlayerState.fromJson(e! as Map<String, Object?>),
      ))
        p.id: p,
    },
    journal: [
      for (final e in j['journal']! as List<Object?>)
        DomainEvent.fromJson(e! as Map<String, Object?>),
    ],
  );
}
