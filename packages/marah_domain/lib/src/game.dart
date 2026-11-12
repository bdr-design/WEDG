import 'catalog/catalog.dart';
import 'catalog/region.dart';
import 'commands.dart';
import 'common/ids.dart';
import 'common/money.dart';
import 'common/result.dart';
import 'common/rng.dart';
import 'common/time.dart';
import 'events.dart';
import 'handlers/handlers.dart' as handlers;
import 'model/game_state.dart';
import 'model/player.dart';
import 'rules/balance.dart';
import 'rules/provisions.dart';
import 'rules/valuation.dart';
import 'sim.dart';
import 'systems/systems.dart';
import 'world_gen.dart';

/// The single entry point to the rules: create a world, apply commands,
/// advance time. Everything else in the package is an implementation detail.
class Game {
  Game(this.state);

  final GameState state;

  GameDay get today => state.world.day;

  /// Starts a new world with one player.
  static Game create({
    required int seed,
    required String playerName,
    required String farmName,
    required Region region,
    required ColorCategory favourite,
    GameDay? startDay,
    DateTime? startedAt,
  }) {
    final ids = IdGenerator(worldSeed: seed & 0x7FFFFFFF);
    final start = startDay ?? GameDay.ofDate(DateTime.utc(2026, 10));
    final world = WorldState(
      seed: seed & 0x7FFFFFFF,
      day: start,
      ids: ids,
      owners: WorldGen.makeOwners(ids),
      camels: {},
      listings: {},
      offers: {},
      studs: {},
      festivals: {},
      plannedUntil: start,
    );
    final playerId = ids.owner();
    final player = PlayerState(
      id: playerId,
      name: playerName,
      cash: Riyal.zero,
      favourite: favourite.name,
      farm: Farm(
        name: farmName,
        region: region,
        capacity: Balance.startingCapacity,
        shepherds: 1,
        feedPlan: FeedPlan.standard,
        storeKg: Balance.startingStoreKg,
        tankL: Balance.startingTankL,
      ),
    );
    final state = GameState(
      world: world,
      players: {playerId: player},
      startedOn: start,
      startedAtUtcMs: (startedAt ?? DateTime.now())
          .toUtc()
          .millisecondsSinceEpoch,
    );
    final sim = Sim(state);
    sim.pay(player, const Riyal(Balance.startingCash), LedgerCategory.opening);

    final gen = WorldGen(sim);
    final rng = sim.rng(['setup']);
    // Starter herd of the chosen colour family.
    for (final (age, mean) in const [
      (6 * 365 + 120, 54.0),
      (4 * 365 + 200, 52.0),
      (2 * 365 + 90, 50.0),
    ]) {
      final c = gen.makeCamel(
        rng,
        owner: playerId,
        mean: mean,
        category: favourite,
        sex: Sex.female,
        ageDays: age,
      );
      c
        ..acquiredOn = start - 200
        ..lastPlayerOwner = playerId
        ..purchasePrice = Valuation.value(c, start).value;
    }
    // a month of the starter herd's needs in store (balance)
    {
      final n = Provisions.needs(
        sim.herdOf(playerId),
        player.farm.feedPlan,
        start,
      );
      player.farm
        ..barleyKg = q2(n.barley * Balance.startingStockDays)
        ..alfalfaKg = q2(n.alfalfa * Balance.startingStockDays)
        ..waterL = q2(n.water * Balance.startingStockDays);
    }
    for (var i = 0; i < 34; i++) {
      gen.addMarketListing(rng);
    }
    for (var i = 0; i < 8; i++) {
      gen.addStud(rng);
    }
    gen.planSeason(start.month >= 9 ? start.year : start.year - 1);
    state.record(sim.drain());
    return Game(state);
  }

  /// The human player (offline there is exactly one).
  PlayerState get me => state.players.values.first;

  /// Applies a command. Returns the events it caused or why it was refused.
  Result dispatch(Command command) {
    final sim = Sim(state);
    final result = handlers.handle(sim, command);
    state.record(result.events);
    return result;
  }

  /// Simulates whole days until [day]. Returns everything that happened.
  List<DomainEvent> advanceTo(GameDay day) {
    final out = <DomainEvent>[];
    final sim = Sim(state);
    while (state.world.day < day) {
      state.world.day = state.world.day + 1;
      for (final system in dailyPipeline) {
        system.run(sim);
      }
      final events = sim.drain();
      state.record(events);
      out.addAll(events);
    }
    return out;
  }

  List<DomainEvent> advanceDays(int days) => advanceTo(today + days);

  /// Brings the world up to the clock (offline: device time at 7× speed).
  List<DomainEvent> catchUp(WorldClock clock) => advanceTo(clock.today());
}
