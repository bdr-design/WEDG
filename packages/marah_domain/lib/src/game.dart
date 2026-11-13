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
import 'model/camel.dart';
import 'model/game_state.dart';
import 'model/player.dart';
import 'rules/balance.dart';
import 'rules/genetics.dart';
import 'rules/names.dart';
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
        shepherds: 0,
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
    // The start (the owner, 13 Nov 2026): one nursing she-camel of the
    // chosen colour family, seven years old, in calf again, and her calf,
    // born and conceived in their season (the owner, 13 Nov: «خلها
    // بموسمها»): (field) camels are bred from November to April
    // (Balance.breedingMonths), so calves come in winter; hers was born on 15
    // January, eight and a half months before the game's 1 October start (its
    // first three months of free nursing behind it, so her milk is sold from
    // the first day). (balance) An ordinary camel, as a beginner's is: bred
    // to a mean of 42 she is worth about 14,500 to 23,000, her pregnancy in
    // it (p10 to p90 over 200 seeds, the review; a 52 had made some
    // starts' camel worth 150,000, more than seven times the money), at the
    // low end of the GDD's 10,000 to 40,000 for مقاني (GDD 6).
    final dam = gen.makeCamel(
      rng,
      owner: playerId,
      mean: 42,
      category: favourite,
      sex: Sex.female,
      ageDays: 7 * 365 + 40,
    );
    // (the latest 15 January at least the free nursing's 90 days back; the
    // game starts on 1 October, and a start between mid-January and mid-April
    // would find the calf past its first year, the dam dry, and from the end
    // of March her due day past: startDay is for tests, and none passes one)
    var born = GameDay.ofDate(DateTime.utc(start.year, 1, 15));
    if (start.daysSince(born) <= Balance.freeNursingDays) {
      born = GameDay.ofDate(DateTime.utc(start.year - 1, 1, 15));
    }
    final calfAge = start.daysSince(born);
    // and in calf again (the owner, 13 Nov 2026: on the rest after calving
    // her next calf came a year and a half later): (field) mated within three
    // months of calving, which shortens the interval between calves to about
    // 15 months (the rest the engine gives every other camel,
    // Balance.postCalvingRestDays, makes the usual 22 to 23 months); here 60
    // days after it, in March, in the season, checked and confirmed, due a
    // gestation later, at the end of March: her milk ends in mid-January, a
    // year from calving, and comes again with the next calf
    final matedOn = born + 60;
    dam
      ..acquiredOn = start - 400
      ..lastPlayerOwner = playerId
      ..calvings = 2
      ..lastCalvedOn = start - calfAge
      ..pregnancy = Pregnancy(
        sire: ParentRef(
          id: sim.world.ids.camel(),
          name: randomCamelName(rng, female: false),
          category: favourite,
        ),
        sireGenes: Genetics.randomGenes(rng, mean: 42),
        matedOn: matedOn,
        checkOn: matedOn + Balance.pregnancyCheckDays,
        dueOn: matedOn + Balance.gestationDays,
        conceived: true,
        confirmed: true,
      );
    final calfSex = rng.chance(0.5) ? Sex.female : Sex.male;
    final calf = Camel(
      id: sim.world.ids.camel(),
      name: randomCamelName(rng, female: calfSex == Sex.female),
      sex: calfSex,
      category: favourite,
      born: start - calfAge,
      ownerId: playerId,
      chip: randomChipNumber(rng),
      genes: Genetics.inherit(
        rng,
        Genetics.randomGenes(rng, mean: 42),
        dam.genes,
        crossbred: false,
      ),
      env: Genetics.randomEnv(rng),
      condition: q2(clampDouble(dam.condition - 2, 45, 90)),
      acquiredOn: start - calfAge,
      lastPlayerOwner: playerId,
      sire: ParentRef(
        id: sim.world.ids.camel(),
        name: randomCamelName(rng, female: false),
        category: favourite,
      ),
      dam: dam.asParent,
    );
    sim.world.camels[calf.id] = calf;
    for (final c in [dam, calf]) {
      c.purchasePrice = Valuation.value(c, start).value;
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
