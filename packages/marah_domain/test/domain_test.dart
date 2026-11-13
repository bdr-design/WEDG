import 'dart:convert';
import 'dart:math' as math;

import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/persistence.dart';
import 'package:marah_domain/src/handlers/handlers.dart' as handlers;
import 'package:marah_domain/src/rules/eligibility.dart';
import 'package:marah_domain/src/rules/genetics.dart';
import 'package:marah_domain/src/rules/judging.dart';
import 'package:marah_domain/src/rules/milk.dart';
import 'package:marah_domain/src/rules/valuation.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:marah_domain/src/systems/systems.dart';
import 'package:marah_domain/src/world_gen.dart';
import 'package:marah_domain/testing.dart';
import 'package:test/test.dart';

Game newGame([int seed = 42]) => Game.create(
  seed: seed,
  playerName: 'بدر',
  farmName: 'عزبة الصفوة',
  region: Region.qassim,
  favourite: ColorCategory.majaheem,
  startedAt: DateTime.utc(2026, 11, 8),
);

String snapshot(Game g) => jsonEncode(g.state.toJson());

Game reload(Game g) =>
    Game(GameState.fromJson(jsonDecode(snapshot(g)) as Map<String, Object?>));

/// Adds a camel to the player's herd that fits [round] of [f] on judging day.
Camel camelFor(
  Game g,
  Festival f,
  ContestRound r, {
  double mean = 70,
  int? daysOldOnJudging,
}) {
  final sim = Sim(g.state);
  // 150 days into the round's age class on judging day, unless told.
  final ageToday =
      (daysOldOnJudging ?? r.age.minDays + 150) - f.judgedOn.daysSince(g.today);
  final c = WorldGen(sim).makeCamel(
    sim.rng(['test-camel', r.id.value]),
    owner: g.me.id,
    mean: mean,
    category: r.category,
    sex: r.sex,
    ageDays: ageToday,
  );
  c.acquiredOn = g.today - 200;
  return c;
}

void expectClean(Game g) => expect(checkInvariants(g.state), isEmpty);

/// The farm's stores filled for a long run: for tests about other things than
/// feed and water, which would otherwise run out.
Game stocked(Game g) {
  g.me.farm
    ..storeKg = 1 << 30
    ..tankL = 1 << 30
    ..barleyKg = 1e8
    ..alfalfaKg = 1e8
    ..waterL = 1e9;
  return g;
}

void main() {
  group('Rng', () {
    test('same seed, same stream; resumable', () {
      final a = Rng(7), b = Rng(7);
      expect(
        [for (var i = 0; i < 5; i++) a.nextUint32()],
        [for (var i = 0; i < 5; i++) b.nextUint32()],
      );
    });

    test('keyed streams are independent of each other', () {
      final x1 = Rng.keyed(1, ['health', 'c1']).nextUint32();
      final x2 = Rng.keyed(1, ['health', 'c2']).nextUint32();
      final x3 = Rng.keyed(1, ['health', 'c1']).nextUint32();
      expect(x1, isNot(x2));
      expect(x1, x3);
    });

    test('normal has the right mean and spread', () {
      final r = Rng(3);
      final xs = [for (var i = 0; i < 20000; i++) r.normal(mean: 10, sd: 2)];
      final mean = xs.reduce((a, b) => a + b) / xs.length;
      final variance =
          xs.map((x) => (x - mean) * (x - mean)).reduce((a, b) => a + b) /
          xs.length;
      expect(mean, closeTo(10, 0.05));
      expect(variance, closeTo(4, 0.15));
    });
  });

  group('Real-time clock', () {
    test('one real day is one game week', () {
      var now = DateTime.utc(2026, 3, 1, 12);
      final clock = RealTimeClock(
        anchorReal: now,
        anchorDay: const GameDay(100),
        now: () => now,
      );
      expect(clock.today(), const GameDay(100));
      now = now.add(const Duration(hours: 24));
      expect(clock.today(), const GameDay(107));
      now = now.add(const Duration(hours: 3, minutes: 26));
      expect(clock.today(), const GameDay(108));
    });

    test('a clock moved backwards never rewinds the world', () {
      final now = DateTime.utc(2026, 3, 1);
      final clock = RealTimeClock(
        anchorReal: now,
        anchorDay: const GameDay(50),
        now: () => now.subtract(const Duration(days: 3)),
      );
      expect(clock.today(), const GameDay(50));
    });
  });

  group('Prices by age in years', () {
    test('as before the age classes were renamed (12 Nov 2026)', () {
      int at(int years) =>
          Valuation.basePrice(AgeClass.fromDays(365 * years + 10), Sex.female);
      expect(
        [for (var y = 0; y <= 25; y++) at(y)],
        [
          7000, 10000, 13000, 16000, 19000, 21000, 22000, 22000, //
          for (var y = 8; y <= 25; y++) 20000,
        ],
      );
    });
  });

  group('Judging weights (GDD 5.3, the owner 12 Nov 2026)', () {
    test(
      'head and neck 25, top 20, forehand 15, hindquarters 10, overall 30',
      () {
        for (final r in JudgedRegion.values) {
          final sum = Trait.values
              .where((t) => t.region == r)
              .fold(0.0, (s, t) => s + t.weight);
          expect((sum * 100).round(), r.points, reason: r.name);
        }
        expect(
          (Trait.values.fold(0.0, (s, t) => s + t.weight) * 1000).round(),
          1000,
        );
      },
    );

    test('the مجاهيم and مغاتير standards differ where the GDD says', () {
      for (final t in [Trait.ears, Trait.back, Trait.fore, Trait.hind]) {
        expect(
          t.describe(ColorCategory.majaheem),
          isNot(t.describe(ColorCategory.wodh)),
          reason: t.name,
        );
      }
      expect(
        Trait.nose.describe(ColorCategory.majaheem),
        Trait.nose.describe(ColorCategory.homr),
      );
    });
  });

  group('Field numbers (research section 6)', () {
    test('gestation stays within 356 to 410 days, near 377 on average', () {
      final g = stocked(newGame(13))..advanceDays(45); // in the breeding season
      final sim = Sim(g.state), gen = WorldGen(sim);
      final days = <int>[];
      for (var i = 0; i < 120; i++) {
        Camel make(Sex sex, int age) => gen.makeCamel(
          sim.rng(['gest', sex.name, i]),
          owner: g.me.id,
          mean: 60,
          category: ColorCategory.homr,
          sex: sex,
          ageDays: age,
        );
        final bull = make(Sex.male, 9 * 365),
            dam = make(Sex.female, 7 * 365)
              ..lastCalvedOn = null
              ..condition = 75;
        expect(
          g.dispatch(MateWithOwnBull(g.me.id, dam.id, bull.id)).ok,
          isTrue,
        );
        final p = dam.pregnancy!;
        days.add(p.dueOn.daysSince(p.matedOn));
      }
      expect(days.every((d) => d >= 356 && d <= 410), isTrue);
      expect(days.reduce((a, b) => a + b) / days.length, closeTo(377, 3));
    });

    test(
      'a female is first mated at 3.3 years (1,209 days), a bull from 5',
      () {
        final g = stocked(newGame(13))
          ..advanceDays(45); // in the breeding season
        final sim = Sim(g.state), gen = WorldGen(sim);
        Camel make(Sex sex, int age, String k) => gen.makeCamel(
          sim.rng(['age-limit', k]),
          owner: g.me.id,
          mean: 60,
          category: ColorCategory.homr,
          sex: sex,
          ageDays: age,
        )..condition = 75;
        final bull = make(Sex.male, 9 * 365, 'bull');
        final under = make(Sex.female, 1208, 'under');
        final at = make(Sex.female, 1209, 'at');
        final r =
            g.dispatch(MateWithOwnBull(g.me.id, under.id, bull.id)) as Err;
        expect(r.error.code, ErrorCode.tooYoungToBreed);
        expect(r.error.params['days'], 1209);
        g.advanceDays(Balance.studRestDays + 1);
        final bull2 = make(Sex.male, 5 * 365 + 1, 'bull5');
        expect(
          g.dispatch(MateWithOwnBull(g.me.id, at.id, bull2.id)).ok,
          isTrue,
        );
        final colt = make(Sex.male, 5 * 365 - 1, 'colt');
        final dam = make(Sex.female, 6 * 365, 'dam');
        final r2 = g.dispatch(MateWithOwnBull(g.me.id, dam.id, colt.id)) as Err;
        expect(r2.error.code, ErrorCode.tooYoungToBreed);
        expect(r2.error.params['days'], 5 * 365);
      },
    );

    test('Tabuk\'s festival is in June', () {
      final tabuk = WorldGen.seasonPlan(2026)
          .firstWhere((e) => e.$2 == Region.tabuk);
      expect((tabuk.$4 - 1) % 12 + 1, 6);
    });

    test(
      'camels fall ill more often in winter and summer, as often a year',
      () {
        final adult = [
          for (final i in Illness.values)
            if (!i.youngOnly && !i.femaleOnly) i,
        ];
        double f(int month) => HealthSystem.seasonFactor(adult, month);
        expect(f(1), greaterThan(f(5)));
        expect(f(8), greaterThan(f(5)));
        var year = 0.0;
        for (var m = 1; m <= 12; m++) {
          year += f(m);
        }
        expect(year / 12, closeTo(1.0, 1e-9));
      },
    );

    test(
      'about 11% of calves die young in their first year besides illness',
      () {
        // the daily chance alone, for calves in condition: 1 - (1 - h)^365
        final g = stocked(newGame(17));
        final sim = Sim(g.state), gen = WorldGen(sim);
        final calves = [
          for (var i = 0; i < 600; i++)
            gen.makeCamel(
              sim.rng(['calf-death', i]),
              owner: g.me.id,
              mean: 55,
              category: ColorCategory.homr,
              sex: i.isEven ? Sex.female : Sex.male,
              ageDays: 0,
            )..condition = 80,
        ];
        g.me.farm.capacity = 1000; // no crowding
        var young = 0;
        for (var d = 0; d < 365; d++) {
          for (final c in calves) {
            if (!c.isAlive) continue;
            c // kept in condition and well: the young cause alone
              ..condition = 80
              ..health = HealthStatus.healthy
              ..illness = null
              ..sickSince = null;
          }
          for (final e in g.advanceDays(1)) {
            if (e is Died && e.cause == DeathCause.young) young++;
          }
        }
        final expected = 1 - math.pow(1 - Balance.calfDailyDeath, 365);
        expect(young / calves.length, closeTo(expected, 0.035));
      },
    );

    test('a contagious illness other than mange spreads through a herd', () {
      final g = stocked(newGame(9));
      final herd = g.state.world.aliveOwnedBy(g.me.id).toList();
      herd.first
        ..health = HealthStatus.sick
        ..illness = Illness.camelpox
        ..sickSince = g.today;
      final caught = <Illness>[];
      for (var d = 0; d < 400 && caught.length < 6; d++) {
        herd.first
          ..health = HealthStatus.sick
          ..illness = Illness.camelpox
          ..sickSince = g.today; // kept sick, untreated
        for (final e in g.advanceDays(1)) {
          if (e is FellSick && e.camel != herd.first.id) caught.add(e.illness);
        }
      }
      expect(caught, contains(Illness.camelpox));
    });

    test('camelpox is commonest in summer, mange in winter', () {
      expect(Illness.camelpox.peakMonths, {7, 8, 9});
      expect(Illness.mange.peakMonths.contains(1), isTrue);
      expect(
        Illness.values.map((i) => i.label),
        containsAll(['جرب', 'القراع', 'الجدري']),
      );
    });
  });

  group('Provisions (GDD 4.3, the owner 12 Nov 2026)', () {
    test('a new farm starts with a month of feed and water', () {
      final g = newGame(3);
      final v = GameView(g.state, g.me.id);
      for (final s in Supply.values) {
        expect(v.daysLeft(s), inInclusiveRange(29, 30), reason: s.name);
      }
    });

    test('an order is paid at the real price and arrives the next day', () {
      final g = newGame(4);
      final cash = g.me.cash.value;
      final r = g.dispatch(OrderSupply(g.me.id, Supply.barley, 10));
      expect(r.ok, isTrue);
      // the bag's price in whole riyals, as the player sees it, times ten
      final bag = (Balance.barleyBagPrice * g.me.farm.region.feed).round();
      expect(cash - g.me.cash.value, bag * 10);
      expect(
        GameView(g.state, g.me.id).unitPrice(Supply.barley).value * 10,
        cash - g.me.cash.value,
      );
      final before = g.me.farm.barleyKg;
      final events = g.advanceDays(1);
      expect(events.whereType<SupplyDelivered>().single.units, 10);
      // ten bags in, a day's ration out
      expect(g.me.farm.barleyKg, greaterThan(before + 400));
    });

    test('the ration is dry matter, ordered by the weight delivered', () {
      final g = newGame(4);
      final adult = g.state.world
          .aliveOwnedBy(g.me.id)
          .firstWhere((c) => c.ageDays(g.today) > 6 * 365);
      final n = Provisions.needs([adult], FeedPlan.standard, g.today);
      // 11 kg of dry matter, 30% of it barley (88% dry), the rest alfalfa (89%)
      expect(n.barley, closeTo(11 * 0.3 / 0.88, 1e-9));
      expect(n.alfalfa, closeTo(11 * 0.7 / 0.89, 1e-9));
      expect(n.barley * 0.88 + n.alfalfa * 0.89, closeTo(11, 1e-9));
    });

    test('a water tanker is 19 tonnes', () {
      expect(Provisions.unitSize(Supply.water), 19000);
      expect(Provisions.unitPrice(Supply.water, Region.qassim), 200);
    });

    test("today's money: the day's entries, not the opening balance", () {
      final g = newGame(4);
      final v = GameView(g.state, g.me.id);
      expect(v.todayNet.value, 0);
      g.dispatch(OrderSupply(g.me.id, Supply.barley, 2));
      expect(v.todayNet.value, -2 * v.unitPrice(Supply.barley).value);
      // the next day starts again from its own entries, and the day's milk
      // (kept in the ledger as one row a month)
      g.advanceDays(2);
      final next = GameView(g.state, g.me.id);
      expect(next.milkIncomeToday, greaterThan(0));
      expect(
        next.todayNet.value,
        g.me.ledger
                .where(
                  (e) =>
                      e.day == next.today && e.category != LedgerCategory.milk,
                )
                .fold(0, (n, e) => n + e.amount.value) +
            next.milkIncomeToday,
      );
    });

    test('a small tanker tops up a tank the large one does not fit', () {
      final g = newGame(4);
      final f = g.me.farm
        ..tankL = 40000
        ..waterL = 31000;
      // 9,000 L of room: not half a 19 t load, a 6 t one and a half
      final v = GameView(g.state, g.me.id);
      expect(v.roomFor(Supply.water), 0);
      expect(v.roomFor(Supply.water, tanker: Tanker.small), 2);
      expect(
        (g.dispatch(OrderSupply(g.me.id, Supply.water, 1)) as Err).error.code,
        ErrorCode.storeFull,
      );
      final cash = g.me.cash.value;
      final r = g.dispatch(
        OrderSupply(g.me.id, Supply.water, 1, tanker: Tanker.small),
      );
      expect(r.ok, isTrue);
      expect(cash - g.me.cash.value, 120);
      final ordered = r.events.whereType<SupplyOrdered>().single;
      expect(ordered.size, 6000);
      final before = f.waterL;
      final events = g.advanceDays(1);
      expect(events.whereType<SupplyDelivered>().single.size, 6000);
      // six tonnes in, a day's drinking out
      expect(f.waterL, greaterThan(before + 6000 - 500));
      expect(f.waterL, lessThanOrEqualTo(before + 6000));
    });

    test('a tanker fills the tank to the top and takes the rest back', () {
      final g = newGame(5);
      final f = g.me.farm..waterL = 2000; // of the start's 6,000 L
      final v = GameView(g.state, g.me.id);
      // 4,000 L of room: more than half a 6 t load
      expect(v.roomFor(Supply.water, tanker: Tanker.small), 1);
      expect(
        g
            .dispatch(
              OrderSupply(g.me.id, Supply.water, 1, tanker: Tanker.small),
            )
            .ok,
        isTrue,
      );
      g.advanceDays(1);
      expect(f.waterL, lessThanOrEqualTo(f.tankL.toDouble()));
      expect(f.waterL, greaterThan(f.tankL - 100.0));
      // with 3,500 L in it, less than half a load of room: not yet
      f.waterL = 3500;
      expect(
        GameView(g.state, g.me.id).roomFor(Supply.water, tanker: Tanker.small),
        0,
      );
      expectClean(g);
    });

    test('the pasture is looked up once a farm a day, and only when dry', () {
      final g = stocked(newGame(4));
      while (g.today.month != 1) {
        g.advanceDays(1);
      }
      Pasture.lookups = 0;
      g.advanceDays(10);
      expect(Pasture.lookups, 0, reason: 'nothing dry: no look-up');
      g.me.farm.waterL = 0;
      g.me.farm.tankL = 0; // and no tanker
      g.advanceDays(1); // the first dry day
      Pasture.lookups = 0;
      g.advanceDays(3);
      expect(Pasture.lookups, 3, reason: 'once a day for the one farm');
    });

    test('the pasture greens in a wet season, and the herd lasts longer', () {
      // winter on dry feed 10 days, on green pasture 17; summer 7 either way
      expect(Balance.thirstDays(1, green: false), 10);
      expect(Balance.thirstDays(1, green: true), 17);
      expect(Balance.thirstDays(7, green: true), 7);
      // green only from December to April, the same each time for a seed,
      // and some seasons wet, some dry
      var greenDays = 0, seasons = <bool>{};
      for (var d = 0; d < 365 * 6; d++) {
        final day = GameDay.ofDate(DateTime.utc(2026, 10)) + d;
        final g = Pasture.green(7, Region.qassim, day);
        expect(g, Pasture.green(7, Region.qassim, day));
        if (g) {
          greenDays++;
          expect(Balance.greenMonths, contains(day.month));
        }
        if (day.month == 1) seasons.add(g);
      }
      expect(greenDays, greaterThan(0));
      expect(seasons, {true, false});
    });

    test('an order that does not fit, or is not paid for, is refused', () {
      final g = newGame(4);
      final room = GameView(g.state, g.me.id).roomFor(Supply.water);
      final r = g.dispatch(OrderSupply(g.me.id, Supply.water, room + 1)) as Err;
      expect(r.error.code, ErrorCode.storeFull);
      expect(r.error.params['room'], room);
      expect(
        (g.dispatch(OrderSupply(g.me.id, Supply.alfalfa, 0)) as Err).error.code,
        ErrorCode.invalidAmount,
      );
      g.me.cash = const Riyal(10);
      expect(
        (g.dispatch(OrderSupply(g.me.id, Supply.barley, 1)) as Err).error.code,
        ErrorCode.insufficientFunds,
      );
    });

    test(
      'unfed and dry, the herd is warned, thins and in time dies of thirst',
      () {
        // the stores run out at the start of November, on dry feed (the
        // pasture greens in December at the earliest): 10 days without water
        final g = newGame(6);
        final events = g.advanceDays(40);
        final low = events.whereType<SupplyLow>().toList();
        expect(low.where((e) => e.days == 3).length, 3);
        expect(low.where((e) => e.days == 0).length, 3);
        expect(g.me.farm.fedShare, 0);
        expect(g.me.farm.dryDays, 10);
        final herd = g.state.world.aliveOwnedBy(g.me.id);
        expect(herd, isNotEmpty, reason: 'none dies within the 10 days');
        for (final c in herd) {
          expect(c.condition, lessThan(60));
        }
        final more = g.advanceDays(30);
        final thirst = more.whereType<Died>().where(
          (d) => d.cause == DeathCause.thirst,
        );
        expect(thirst, isNotEmpty);
        // none before the herd has gone 10 days dry
        final firstDry = events.whereType<SupplyLow>().firstWhere(
          (e) => e.supply == Supply.water && e.days == 0,
        );
        expect(
          thirst.first.day.daysSince(firstDry.day),
          greaterThanOrEqualTo(10),
        );
      },
    );

    test('going short warns even when the need jumps past a low stock', () {
      final g = newGame(5);
      final v = GameView(g.state, g.me.id);
      g.me.farm.waterL = v.dailyNeeds.water * 0.4; // under half a day
      final events = g.advanceDays(1);
      expect(
        events.whereType<SupplyLow>().where(
          (e) => e.supply == Supply.water && e.days == 0,
        ),
        hasLength(1),
      );
      expect(g.me.farm.dryDays, 1);
      expect(g.advanceDays(3).whereType<SupplyLow>(), isEmpty); // once
    });

    test('a day on half the water holds the dry count, a full day ends it', () {
      final g = stocked(newGame(5));
      final v = GameView(g.state, g.me.id);
      for (var d = 0; d < 4; d++) {
        g.me.farm.waterL = 0;
        g.advanceDays(1);
      }
      expect(g.me.farm.dryDays, 4);
      g.me.farm.waterL = v.dailyNeeds.water * 0.6;
      g.advanceDays(1);
      expect(g.me.farm.dryDays, 4);
      g.me.farm.waterL = v.dailyNeeds.water * 2;
      g.advanceDays(1);
      expect(g.me.farm.dryDays, 0);
    });

    test('in summer a herd without water dies within days of its limit', () {
      final g = stocked(newGame(5));
      g.advanceTo(GameDay.ofDate(DateTime.utc(2027, 6, 1)));
      stocked(g).me.farm.waterL = 0;
      g.me.farm.tankL = 1 << 30;
      final alive = g.state.world.aliveOwnedBy(g.me.id).length;
      expect(alive, greaterThan(0));
      // the tank kept empty: 7 days a camel can go in summer, then deaths
      for (var d = 0; d < 20; d++) {
        g.me.farm.waterL = 0;
        g.advanceDays(1);
      }
      expect(g.state.world.aliveOwnedBy(g.me.id), isEmpty);
    });

    test('a nursing camel drinks 42 L; a 30 t tank built adds to the tank', () {
      final g = newGame(7);
      final dam = g.state.world
          .aliveOwnedBy(g.me.id)
          .firstWhere((c) => c.lastCalvedOn != null);
      expect(Provisions.waterFor(dam, g.today), 42);
      final tank = g.me.farm.tankL, cash = g.me.cash.value;
      expect(g.dispatch(BuildFacility(g.me.id, Facility.tank)).ok, isTrue);
      expect(g.me.cash.value, cash - Facility.tank.price);
      g.advanceDays(Balance.buildDays - 1);
      expect(g.me.farm.tankL, tank, reason: 'not done before its day');
      g.advanceDays(1);
      expect(g.me.farm.tankL - tank, 30000);
      expect(g.me.farm.has(Facility.tank), 1);
      expect(
        (g.dispatch(BuildFacility(g.me.id, Facility.tank)) as Err).error.code,
        ErrorCode.alreadyBuilt,
      );
      expectClean(g);
    });
  });

  group('Milk and the farm that grows (the owner, 13 Nov 2026)', () {
    Camel damOf(Game g) => g.state.world
        .aliveOwnedBy(g.me.id)
        .firstWhere((c) => c.lastCalvedOn != null && c.sex == Sex.female);
    Camel calfOf(Game g) => g.state.world
        .aliveOwnedBy(g.me.id)
        .firstWhere((c) => c.dam != null && c.dam!.id == damOf(g).id);

    test('the milk is sold each day; the calf keeps its share', () {
      final g = stocked(newGame(21))..advanceDays(1);
      final v = GameView(g.state, g.me.id);
      final m = v.milk.single;
      expect(m.litres, inInclusiveRange(2.5, 9.5));
      expect(m.sold, closeTo(m.litres * (1 - CalfShare.half.part), 1e-9));
      expect(v.milkIncomeToday, (m.sold * Balance.milkPrice).round());
      final cash = g.me.cash.value;
      g.advanceDays(1);
      final v2 = GameView(g.state, g.me.id);
      expect(g.me.cash.value - cash, v2.milkIncomeToday);
      expect(v2.milkThisMonth.value, greaterThan(0));
      expectClean(g);
    });

    test(
      'all of it to the calf sells none; a quarter sells more than half',
      () {
        int income(CalfShare share) {
          final g = stocked(newGame(22));
          g.dispatch(SetCalfShare(g.me.id, share));
          g.advanceDays(10);
          return g.me.ledger
              .where((e) => e.category == LedgerCategory.milk)
              .fold(0, (n, e) => n + e.amount.value);
        }

        expect(income(CalfShare.all), 0);
        expect(income(CalfShare.quarter), greaterThan(income(CalfShare.half)));
      },
    );

    test('the calf grows better on more of the milk', () {
      double condition(CalfShare share) {
        final g = stocked(newGame(23));
        g.dispatch(SetCalfShare(g.me.id, share));
        g.advanceDays(60);
        return calfOf(g).condition;
      }

      expect(
        condition(CalfShare.all),
        greaterThan(condition(CalfShare.quarter) + 4),
      );
    });

    test('a calf without its dam does worst of all; no wages without a '
        'shepherd', () {
      double condition(CalfShare? share) {
        final g = stocked(newGame(27));
        if (share == null) {
          final dam = damOf(g);
          expect(g.dispatch(QuickSale(g.me.id, dam.id)).ok, isTrue);
        } else {
          g.dispatch(SetCalfShare(g.me.id, share));
        }
        final events = g.advanceDays(60);
        expect(events.whereType<WagesPaid>(), isEmpty);
        return g.state.world
            .aliveOwnedBy(g.me.id)
            .firstWhere((c) => c.dam != null && c.ageDays(g.today) < 365)
            .condition;
      }

      expect(condition(null), lessThan(condition(CalfShare.quarter)));
    });

    test('a tanker that does not fit takes the rest back, and says so', () {
      final g = newGame(28);
      g.me.farm.waterL = 2500; // 3,500 L of room in the start's 6,000 L tank
      expect(
        g
            .dispatch(
              OrderSupply(g.me.id, Supply.water, 1, tanker: Tanker.small),
            )
            .ok,
        isTrue,
      );
      final drunk = GameView(g.state, g.me.id).dailyNeeds.water;
      final ev = g.advanceDays(1).whereType<SupplyDelivered>().single;
      // what did not fit, as the tank stood before the day's drinking
      expect(ev.returned, 2500);
      expect(g.me.farm.waterL, closeTo(6000 - drunk, 1));
    });

    test('without her calf all the milk is sold; dry after a year', () {
      final g = stocked(newGame(24));
      final calf = calfOf(g);
      expect(g.dispatch(QuickSale(g.me.id, calf.id)).ok, isTrue);
      g.advanceDays(1);
      final m = GameView(g.state, g.me.id).milk.single;
      expect(m.calf, isNull);
      expect(m.sold, m.litres);
      // a year from calving she is dry
      final dam = damOf(g);
      g.advanceDays(
        Balance.lactationDays - g.today.daysSince(dam.lastCalvedOn!),
      );
      expect(Milk.inMilkDays(dam, g.today), isNull);
      expect(GameView(g.state, g.me.id).milk, isEmpty);
    });

    test('a she-camel gives about 5 L a day over her lactation (the real '
        'common average)', () {
      final g = newGame(25);
      final sim = Sim(g.state);
      final gen = WorldGen(sim);
      final rng = sim.rng(['milk-test']);
      var sum = 0.0, n = 0;
      for (var i = 0; i < 300; i++) {
        final c = gen.makeCamel(
          rng,
          owner: g.me.id,
          mean: 50,
          category: ColorCategory.wodh,
          sex: Sex.female,
          ageDays: 6 * 365,
        );
        for (var d = 0; d < Balance.lactationDays; d += 5) {
          sum += Milk.level(c, g.state.world.seed) * Milk.shape(d);
          n++;
        }
      }
      expect(sum / n, inInclusiveRange(4.0, 5.5));
    });

    test('the player tends up to ten head; past it shepherds and their '
        'caravan', () {
      expect(CareSystem.shepherdsNeeded(2), 0);
      expect(CareSystem.shepherdsNeeded(Balance.ownerTendsUpTo), 0);
      expect(CareSystem.shepherdsNeeded(Balance.ownerTendsUpTo + 1), 1);
      expect(CareSystem.shepherdsNeeded(60), 3);
    });

    test('a facility is paid on ordering, built in three days, and no more '
        'than its most', () {
      final g = stocked(newGame(26));
      final sim = Sim(g.state);
      sim.pay(g.me, const Riyal(200000), LedgerCategory.sale);
      final store = g.me.farm.storeKg;
      expect(g.dispatch(BuildFacility(g.me.id, Facility.store)).ok, isTrue);
      expect(
        (g.dispatch(BuildFacility(g.me.id, Facility.store)) as Err).error.code,
        ErrorCode.alreadyBuilt,
        reason: 'one being built counts',
      );
      g.advanceDays(Balance.buildDays);
      expect(g.me.farm.storeKg, store + 10000);
      for (var i = 0; i < Facility.pen.most; i++) {
        expect(g.dispatch(BuildFacility(g.me.id, Facility.pen)).ok, isTrue);
      }
      expect(
        (g.dispatch(BuildFacility(g.me.id, Facility.pen)) as Err).error.code,
        ErrorCode.alreadyBuilt,
      );
      g.advanceDays(Balance.buildDays);
      expect(
        g.me.farm.capacity,
        Balance.startingCapacity + 10 * Facility.pen.most,
      );
      expect(g.dispatch(BuildFacility(g.me.id, Facility.caravan)).ok, isTrue);
      expect(
        (g.dispatch(SetShepherds(g.me.id, 1)) as Err).error.code,
        ErrorCode.needsFacility,
        reason: 'the caravan is not done yet',
      );
      g.advanceDays(Balance.buildDays);
      expect(g.dispatch(SetShepherds(g.me.id, 1)).ok, isTrue);
      expect(snapshot(reload(g)), snapshot(g));
      expectClean(g);
    });
  });

  group('Colour families', () {
    test('the festival\'s six, مغاتير covering the five light ones', () {
      expect(ColorCategory.values.map((c) => c.label).toList(), [
        'مجاهيم',
        'وضح',
        'شقح',
        'شعل',
        'صفر',
        'حمر',
      ]);
      expect(ColorCategory.values.where((c) => c.isMaghateer).length, 5);
      expect(ColorCategory.majaheem.isMaghateer, isFalse);
    });
  });

  group('Age classes', () {
    test('map completed years to Gulf names', () {
      expect(AgeClass.fromDays(100), AgeClass.hwar);
      expect(AgeClass.fromDays(200), AgeClass.makhlool);
      expect(AgeClass.fromDays(365 + 10), AgeClass.mafrood);
      expect(
        AgeClass.fromDays(365 * 2 + 10),
        AgeClass.haq,
      ); // حق before لقي (the owner, 12 Nov 2026)
      expect(AgeClass.fromDays(365 * 3 + 10), AgeClass.laqi);
      expect(AgeClass.fromDays(365 * 4 + 10).labelFor(Sex.female), 'جذعة');
      expect(AgeClass.fromDays(365 * 9), AgeClass.fater);
      expect(AgeClass.fromDays(365 * 12).labelFor(Sex.male), 'عود');
      expect(AgeClass.fromDays(365 * 12).labelFor(Sex.female), 'ناب');
      expect(AgeClass.fromDays(365 * 21), AgeClass.harish);
      // each class starts on its first day, the day before is the class before
      for (final a in AgeClass.values.skip(1)) {
        expect(AgeClass.fromDays(a.minDays), a);
        expect(AgeClass.fromDays(a.minDays - 1).index, a.index - 1);
      }
      for (var y = 1; y <= 25; y++) {
        expect(AgeClass.fromDays(365 * y).minDays, lessThanOrEqualTo(365 * y));
      }
      // every day falls in exactly one class, in order
      var last = AgeClass.hwar;
      for (var d = 0; d < 365 * 25; d++) {
        final a = AgeClass.fromDays(d);
        expect(a.index >= last.index && a.index <= last.index + 1, isTrue);
        last = a;
      }
    });
  });

  group('Genetics', () {
    test('calves centre on the mid-parent value', () {
      final rng = Rng(3);
      final sire = {for (final t in Trait.values) t: 80.0};
      final dam = {for (final t in Trait.values) t: 60.0};
      var sum = 0.0;
      for (var i = 0; i < 600; i++) {
        sum += Judging.geneticQuality(
          Genetics.inherit(rng, sire, dam, crossbred: false),
        );
      }
      expect(sum / 600, closeTo(70, 0.8));
    });

    test('crossing colour families lowers coat colour', () {
      final rng = Rng(9);
      final g = {for (final t in Trait.values) t: 70.0};
      var pure = 0.0, cross = 0.0;
      for (var i = 0; i < 300; i++) {
        pure += Genetics.inherit(rng, g, g, crossbred: false)[Trait.coat]!;
        cross += Genetics.inherit(rng, g, g, crossbred: true)[Trait.coat]!;
      }
      expect((pure - cross) / 300, closeTo(Genetics.crossCoatPenalty, 1.5));
    });
  });

  group('New game', () {
    test('starts with one nursing camel and her calf, a market, studs and a '
        'season', () {
      final g = newGame();
      final v = GameView(g.state, g.me.id);
      expect(v.herd, hasLength(2));
      expect(v.herd.every((c) => c.category == ColorCategory.majaheem), isTrue);
      final dam = v.herd.firstWhere((c) => c.lastCalvedOn != null);
      final calf = v.herd.firstWhere((c) => c.id != dam.id);
      expect(dam.sex, Sex.female);
      expect(calf.dam!.id, dam.id);
      expect(calf.born, dam.lastCalvedOn);
      expect(calf.ageDays, greaterThanOrEqualTo(Balance.freeNursingDays));
      expect(g.me.farm.shepherds, 0);
      expect(g.me.farm.capacity, Balance.startingCapacity);
      expect(g.me.farm.tankL, Balance.startingTankL);
      expect(v.milk, hasLength(1));
      expect(v.milk.single.calf!.id, calf.id);
      // in calf again (the owner, 13 Nov): due about ten and a half months in
      expect(dam.pregnant, isTrue);
      expect(dam.dueOn!.daysSince(g.today), Balance.gestationDays - 60);
      expect(v.market.length, greaterThan(20));
      expect(v.studs, isNotEmpty);
      expect(v.festivals, isNotEmpty);
      expect(g.me.cash.value, Balance.startingCash);
      expectClean(g);
    });
  });

  group('Saving', () {
    test('a save reads back to the identical state', () {
      final g = newGame()..advanceDays(60);
      expect(snapshot(reload(g)), snapshot(g));
    });

    test('saving and reloading mid-game never changes what happens', () {
      for (final seed in [1, 2, 3]) {
        final straight = newGame(seed);
        final bot1 = Bot(straight);
        var reloaded = newGame(seed);
        for (var week = 0; week < 104; week++) {
          bot1.week();
          Bot(reloaded).week();
          if (week % 5 == 0) reloaded = reload(reloaded);
        }
        expect(snapshot(reloaded), snapshot(straight), reason: 'seed $seed');
      }
    });
  });

  group('Events', () {
    test('news keeps coming after the stored history is full', () {
      // a farm with a shepherd (his caravan built), so wages are paid every
      // month (none are paid with no shepherd)
      final g = stocked(newGame());
      Sim(g.state).pay(g.me, const Riyal(100000), LedgerCategory.sale);
      expect(g.dispatch(BuildFacility(g.me.id, Facility.caravan)).ok, isTrue);
      g.advanceDays(Balance.buildDays);
      expect(g.dispatch(SetShepherds(g.me.id, 1)).ok, isTrue);
      g.advanceDays(365 * 3);
      expect(
        g.state.inboxOf(g.me.id).length,
        lessThanOrEqualTo(GameState.inboxLimit),
      );
      final later = g.advanceDays(31);
      expect(later.whereType<WagesPaid>(), isNotEmpty);
    });
  });

  group('Market', () {
    test('buying pays ask plus transport and moves the camel', () {
      final g = newGame();
      Sim(g.state).pay(g.me, const Riyal(200000), LedgerCategory.sale);
      final v = GameView(g.state, g.me.id);
      final l = v.market.firstWhere((l) => l.askPrice.value < 150000);
      final cash = g.me.cash;
      final r = g.dispatch(BuyListing(g.me.id, l.id));
      expect(r.ok, isTrue, reason: '$r');
      expect(g.me.cash, cash - l.askPrice - l.transport);
      expect(GameView(g.state, g.me.id).camel(l.camel.id)!.isMine, isTrue);
      expect(g.state.world.listings.containsKey(l.id), isFalse);
      expect(r.events.single, isA<CamelBought>());
      expectClean(g);
    });

    test('refused without money or space', () {
      final g = newGame();
      final l = GameView(g.state, g.me.id).market.first;
      g.me.cash = const Riyal(100);
      final r = g.dispatch(BuyListing(g.me.id, l.id)) as Err;
      expect(r.error.code, ErrorCode.insufficientFunds);

      final g2 = newGame();
      g2.me
        ..cash = const Riyal(10000000)
        ..farm.capacity = 2;
      final l2 = GameView(g2.state, g2.me.id).market.first;
      final r2 = g2.dispatch(BuyListing(g2.me.id, l2.id)) as Err;
      expect(r2.error.code, ErrorCode.farmFull);
    });

    test('bargaining: rejected, countered, then accepted at the floor', () {
      final g = newGame();
      final l = GameView(g.state, g.me.id).market.first;
      final listing = g.state.world.listings[l.id]!;
      final reserve = listing.reservePrice.value;

      final low =
          g.dispatch(Bargain(g.me.id, l.id, (reserve * 0.5).round())) as Err;
      expect(low.error.code, ErrorCode.bargainRejected);

      final mid =
          g.dispatch(Bargain(g.me.id, l.id, (reserve * 0.9).round())) as Err;
      expect(mid.error.code, ErrorCode.bargainCountered);
      expect(listing.askPrice.value, greaterThanOrEqualTo(reserve));

      final cash = g.me.cash.value;
      final ok = g.dispatch(Bargain(g.me.id, l.id, reserve));
      expect(ok.ok, isTrue);
      expect(cash - g.me.cash.value, reserve + l.transport.value);
      expectClean(g);
    });

    test('a failed purchase does not use up a bargaining attempt', () {
      final g = newGame();
      final l = GameView(g.state, g.me.id).market.first;
      final reserve = g.state.world.listings[l.id]!.reservePrice.value;
      g.me.cash = const Riyal(10);
      g.dispatch(Bargain(g.me.id, l.id, reserve));
      expect(
        GameView(g.state, g.me.id).bargainsLeft(l.id),
        Balance.maxBargainsPerBuyer,
      );
    });

    test('short of money, every bid is refused alike, the floor unread', () {
      // over the floor or under it, a bid the player cannot pay for is
      // refused for the money and uses no try (the review read the floor by
      // halving: over it refused for money, under it answered)
      final g = newGame();
      final l = GameView(g.state, g.me.id).market.first;
      final reserve = g.state.world.listings[l.id]!.reservePrice.value;
      g.me.cash = const Riyal(500);
      for (final bid in [reserve + 500, reserve - 500, reserve ~/ 2]) {
        final r = g.dispatch(Bargain(g.me.id, l.id, bid)) as Err;
        expect(r.error.code, ErrorCode.insufficientFunds);
      }
      expect(
        GameView(g.state, g.me.id).bargainsLeft(l.id),
        Balance.maxBargainsPerBuyer,
      );
      final full = newGame();
      full.me
        ..cash = const Riyal(10000000)
        ..farm.capacity = 2;
      final l2 = GameView(full.state, full.me.id).market.first;
      final r2 = full.dispatch(Bargain(full.me.id, l2.id, 1000)) as Err;
      expect(r2.error.code, ErrorCode.farmFull);
    });

    test('the herd\'s worth is the appraisals\', not the exact values', () {
      final g = newGame();
      Sim(g.state).pay(g.me, const Riyal(400000), LedgerCategory.sale);
      final l = GameView(
        g.state,
        g.me.id,
      ).market.firstWhere((l) => l.askPrice.value < 150000);
      expect(g.dispatch(BuyListing(g.me.id, l.id)).ok, isTrue);
      final v = GameView(g.state, g.me.id);
      final exact = g.state.world
          .aliveOwnedBy(g.me.id)
          .fold<int>(0, (a, c) => a + Valuation.value(c, g.today).value);
      final heard = g.state.world
          .aliveOwnedBy(g.me.id)
          .fold<double>(
            0,
            (a, c) =>
                a + CamelView.appraise(c, g.today, g.me.id, g.state.world.seed),
          );
      expect(v.herdValue, marketRound(heard));
      expect(v.herdValue.value, isNot(exact));
    });

    test('seller stops after three bargains', () {
      final g = newGame();
      final l = GameView(g.state, g.me.id).market.first;
      for (var i = 0; i < 3; i++) {
        g.dispatch(Bargain(g.me.id, l.id, 1000));
      }
      final r = g.dispatch(Bargain(g.me.id, l.id, 1000)) as Err;
      expect(r.error.code, ErrorCode.sellerRefusesBargaining);
    });

    test('listing attracts offers; accepting pays price minus commission', () {
      final g = newGame(5);
      final c = GameView(g.state, g.me.id).herd.first;
      final (lo, _) = c.estimate;
      expect(g.dispatch(ListForSale(g.me.id, c.id, lo.value)).ok, isTrue);
      Offer? offer;
      for (var i = 0; i < 40 && offer == null; i++) {
        g.advanceDays(1);
        offer = g.state.world.offers.values.firstOrNull;
      }
      expect(offer, isNotNull);
      final cash = g.me.cash.value;
      expect(g.dispatch(AcceptOffer(g.me.id, offer!.id)).ok, isTrue);
      final commission = (offer.amount.value * Balance.brokerCommission)
          .round();
      expect(g.me.cash.value - cash, offer.amount.value - commission);
      expect(GameView(g.state, g.me.id).camel(c.id)!.isMine, isFalse);
      expectClean(g);
    });

    test('quick sale pays less than the market', () {
      final g = newGame();
      final v = GameView(g.state, g.me.id);
      final c = v.herd.first;
      final price = v.quickSalePrice(c.id)!;
      final value = Valuation.value(g.state.world.camels[c.id]!, g.today);
      expect(price.value, lessThan(value.value));
      final cash = g.me.cash.value;
      expect(g.dispatch(QuickSale(g.me.id, c.id)).ok, isTrue);
      // the price shown is the price paid: the broker buys it himself and
      // takes no commission
      expect(g.me.cash.value - cash, price.value);
      expect(GameView(g.state, g.me.id).herd, hasLength(1));
      expectClean(g);
    });

    test('the broker\'s price is his own eye, not the value read back', () {
      // over the market's camels, his price over the factor is off the true
      // value by a few percent, differently for each, and steady in a week
      final g = newGame();
      final sim = Sim(g.state);
      final offs = <double>[];
      for (final l in g.state.world.listings.values) {
        final c = g.state.world.camels[l.camelId]!;
        final value = Valuation.value(c, g.today).value;
        final price = handlers.quickSalePrice(c, sim).value;
        offs.add(price / Balance.quickSaleFactor / value - 1);
        expect(price, lessThan(value));
      }
      expect(offs.where((o) => o.abs() > 0.02), isNotEmpty);
      expect(
        offs.every((o) => o.abs() <= 2.5 * Balance.brokerEyeSd + 0.02),
        isTrue,
      );
      final c =
          g.state.world.camels[g.state.world.listings.values.first.camelId]!;
      final d0 = g.today.value;
      final week = d0 - d0 % 7;
      int on(int day) {
        final was = g.state.world.day;
        g.state.world.day = GameDay(day);
        final eye =
            handlers.quickSalePrice(c, Sim(g.state)).value /
            Valuation.value(c, GameDay(day)).value;
        g.state.world.day = was;
        return (eye * 1000).round();
      }

      expect(on(week), on(week + 6));
    });

    test('a bought camel comes on the truck the next day', () {
      final g = newGame();
      Sim(g.state).pay(g.me, const Riyal(400000), LedgerCategory.sale);
      final l = GameView(g.state, g.me.id).market.firstWhere(
        (l) => l.askPrice.value < 150000 && l.camel.sex == Sex.female,
      );
      expect(g.dispatch(BuyListing(g.me.id, l.id)).ok, isTrue);
      var c = GameView(g.state, g.me.id).camel(l.camel.id)!;
      expect(c.isMine, isTrue);
      expect(c.onTheWay, isTrue);
      // not for sale or breeding while on the truck, and not milked today
      final sell = g.dispatch(QuickSale(g.me.id, c.id)) as Err;
      expect(sell.error.code, ErrorCode.onTheWay);
      final list = g.dispatch(ListForSale(g.me.id, c.id, 50000)) as Err;
      expect(list.error.code, ErrorCode.onTheWay);
      expect(
        Eligibility.femaleCanBreed(g.state.world.camels[c.id]!, g.today)?.code,
        ErrorCode.onTheWay,
      );
      expect(
        GameView(g.state, g.me.id).milk.where((m) => m.camel.id == c.id),
        isEmpty,
      );
      g.advanceDays(1);
      c = GameView(g.state, g.me.id).camel(c.id)!;
      expect(c.onTheWay, isFalse);
      expect(GameView(g.state, g.me.id).canSell(c.id), isNull);
      expectClean(g);
    });
  });

  group('Breeding', () {
    test('out of season is refused', () {
      final g = newGame(); // 1 October
      final f = GameView(
        g.state,
        g.me.id,
      ).herd.firstWhere((c) => c.ageDays > 6 * 365);
      // past her rest after calving and empty (the start's camel calved 120
      // days ago and is in calf again)
      g.state.world.camels[f.id]!
        ..lastCalvedOn = g.today - 400
        ..pregnancy = null;
      final stud = g.state.world.studs.values.first;
      final r = g.dispatch(MateWithStud(g.me.id, f.id, stud.id)) as Err;
      expect(r.error.code, ErrorCode.notBreedingSeason);
    });

    test('a stud that is not on offer cannot be used', () {
      final g = stocked(newGame())..advanceDays(45);
      final f = GameView(
        g.state,
        g.me.id,
      ).herd.firstWhere((c) => c.ageDays > 6 * 365);
      final r =
          g.dispatch(MateWithStud(g.me.id, f.id, const StudId('nope'))) as Err;
      expect(r.error.code, ErrorCode.studUnavailable);
    });

    test(
      'mating charges fee and transport, then a calf about 13 months on',
      () {
        final g = stocked(newGame(11))..advanceDays(45); // mid-November
        final dam = g.state.world.camels.values.firstWhere(
          (c) => c.ownerId == g.me.id && c.ageYears(g.today) >= 6,
        );
        dam.lastCalvedOn = null;
        for (
          var attempt = 0;
          attempt < 12 && !dam.pregnancyConfirmed;
          attempt++
        ) {
          final stud = g.state.world.studs.values.firstWhere(
            (s) => s.until > g.today + 30,
          );
          final cash = g.me.cash.value;
          final r = g.dispatch(MateWithStud(g.me.id, dam.id, stud.id));
          expect(r.ok, isTrue, reason: '$r');
          final move = Balance.transportCost(
            stud.region.roadKmTo(g.me.farm.region),
            1,
          );
          expect(cash - g.me.cash.value, stud.fee.value + move);
          g.advanceDays(Balance.pregnancyCheckDays + Balance.studRestDays);
        }
        expect(dam.pregnancyConfirmed, isTrue);
        final sireId = dam.pregnancy!.sire.id;
        final gestation = dam.pregnancy!.dueOn.daysSince(
          dam.pregnancy!.matedOn,
        );
        expect(gestation, inInclusiveRange(375, 395));
        final events = g.advanceTo(dam.pregnancy!.dueOn);
        expect(dam.calvings, greaterThan(0));
        final born = events.whereType<CalfBorn>();
        final lost = events.whereType<CalfLost>();
        expect(born.length + lost.length, 1);
        if (born.isNotEmpty) {
          final calf = g.state.world.camels[born.single.camel]!;
          expect(calf.sire!.id, sireId);
          expect(calf.dam!.id, dam.id);
          expect(calf.homeBred, isTrue);
        }
        expectClean(g);
      },
    );
  });

  group('Health', () {
    test('treatment costs money and the camel recovers', () {
      final g = newGame();
      final c = g.state.world.camels.values.firstWhere(
        (c) => c.ownerId == g.me.id,
      );
      c
        ..health = HealthStatus.sick
        ..illness = Illness.pneumonia
        ..sickSince = g.today;
      final cash = g.me.cash.value;
      expect(g.dispatch(Treat(g.me.id, c.id)).ok, isTrue);
      expect(g.me.cash.value, lessThan(cash));
      g.advanceDays(Illness.pneumonia.recoverDays + 1);
      expect(c.health, HealthStatus.healthy);
      expectClean(g);
    });

    test('a sick camel left untreated for long often dies', () {
      var deaths = 0;
      for (var seed = 1; seed <= 20; seed++) {
        final g = newGame(seed);
        final c = g.state.world.camels.values.firstWhere(
          (c) => c.ownerId == g.me.id,
        );
        c
          ..health = HealthStatus.sick
          ..illness = Illness.trypanosomiasis
          ..sickSince = g.today;
        g.advanceDays(60);
        if (!c.isAlive) deaths++;
        expectClean(g);
      }
      expect(deaths, greaterThan(5));
    });
  });

  group('Contests', () {
    test('entry rules: category, sex, age on judging day, ownership', () {
      final g = newGame(21);
      final f = g.state.world.festivals.values.first;
      final r = f.rounds.first;
      final fits = camelFor(g, f, r);
      final v = GameView(g.state, g.me.id);
      g.advanceTo(f.opensOn);
      expect(v.canEnter(f.id, r.id, fits.id), isNull);

      final wrong = f.rounds.firstWhere(
        (x) => x.category != r.category,
        orElse: () => f.rounds.firstWhere((x) => x.age != r.age),
      );
      expect(
        GameView(g.state, g.me.id).canEnter(f.id, wrong.id, fits.id),
        isNotNull,
      );

      fits.acquiredOn = g.today; // just bought
      expect(
        GameView(g.state, g.me.id).canEnter(f.id, r.id, fits.id)?.code,
        ErrorCode.ownershipTooRecent,
      );
    });

    test(
      'the eldest round (فاطر) takes every older camel, as "mature" did',
      () {
        final g = newGame(3);
        final f = g.state.world.festivals.values.firstWhere(
          (f) => f.rounds.any((r) => r.age == AgeClass.fater),
        );
        final r = f.rounds.firstWhere((r) => r.age == AgeClass.fater);
        final view = GameView(g.state, g.me.id);
        g.advanceTo(f.opensOn);
        for (final years in [9, 11, 15, 22]) {
          final c = camelFor(g, f, r, daysOldOnJudging: 365 * years + 30);
          expect(
            view.canEnter(f.id, r.id, c.id),
            isNull,
            reason: '$years years',
          );
        }
        final young = camelFor(g, f, r, daysOldOnJudging: 365 * 7 + 30);
        expect(
          GameView(g.state, g.me.id).canEnter(f.id, r.id, young.id)?.code,
          ErrorCode.wrongAgeClass,
        );
      },
    );

    test('judging places the entry, pays prizes and records the placing', () {
      final g = newGame(21);
      final f = g.state.world.festivals.values.first;
      final r = f.rounds.first;
      final strong = camelFor(g, f, r, mean: 95)..condition = 90;
      g.advanceTo(f.opensOn);
      expect(g.dispatch(EnterRound(g.me.id, f.id, r.id, strong.id)).ok, isTrue);
      final cash = g.me.cash.value;
      final events = g.advanceTo(f.judgedOn);
      expect(f.done, isTrue);
      final placed = events.whereType<Placed>().single;
      final rank = placed.rank;
      expect(rank, lessThanOrEqualTo(3), reason: 'an elite camel should place');
      expect(strong.placings.single.rank, rank);
      final prize = ContestRules.prizes(f.tier, r.age)[rank - 1];
      final transport =
          Balance.transportCost(g.me.farm.region.roadKmTo(f.region), 1) * 2;
      expect(g.me.cash.value, isNot(cash));
      expect(r.results!.any((row) => row.camelId == strong.id), isTrue);
      expect(
        g.me.ledger.any(
          (l) => l.category == LedgerCategory.prize && l.amount.value == prize,
        ),
        isTrue,
      );
      expect(
        g.me.ledger.any(
          (l) =>
              l.category == LedgerCategory.transport &&
              l.amount.value == -transport,
        ),
        isTrue,
      );
      expectClean(g);
    });

    test('a sick entry is disqualified at the vet check', () {
      final g = newGame(21);
      final f = g.state.world.festivals.values.first;
      final r = f.rounds.first;
      final c = camelFor(g, f, r);
      g.advanceTo(f.opensOn);
      g.dispatch(EnterRound(g.me.id, f.id, r.id, c.id));
      g.advanceTo(f.judgedOn - 1);
      c
        ..health = HealthStatus.sick
        ..illness = Illness.lameness
        ..sickSince = g.today;
      final events = g.advanceDays(1);
      expect(events.whereType<DisqualifiedSick>(), isNotEmpty);
      expect(r.results!.any((row) => row.camelId == c.id), isFalse);
    });
  });

  group('Long run', () {
    test('three years with an active player keeps every invariant', () {
      for (final seed in [3, 4, 5]) {
        final bot = Bot(newGame(seed));
        expect(bot.run(52 * 3), isNull, reason: 'seed $seed');
        expect(bot.commands, greaterThan(20));
      }
    });
  });
  group('Farm and listing commands', () {
    test('cancel a listing and decline an offer', () {
      final g = newGame(5);
      final c = GameView(g.state, g.me.id).herd.first;
      g.dispatch(ListForSale(g.me.id, c.id, c.estimate.$1.value));
      final l = GameView(g.state, g.me.id).myListings.single;
      Offer? offer;
      for (var i = 0; i < 40 && offer == null; i++) {
        g.advanceDays(1);
        offer = g.state.world.offers.values.firstOrNull;
      }
      expect(g.dispatch(DeclineOffer(g.me.id, offer!.id)).ok, isTrue);
      expect(g.state.world.offers.containsKey(offer.id), isFalse);
      expect(g.dispatch(CancelListing(g.me.id, l.id)).ok, isTrue);
      expect(GameView(g.state, g.me.id).myListings, isEmpty);
      expect(GameView(g.state, g.me.id).canSell(c.id), isNull);
      expectClean(g);
    });

    test('cannot cancel or accept on someone else\'s listing', () {
      final g = newGame();
      final other = GameView(g.state, g.me.id).market.first;
      final r = g.dispatch(CancelListing(g.me.id, other.id)) as Err;
      expect(r.error.code, ErrorCode.notYourListing);
    });

    test('rename, feed plan, shepherds and expansion', () {
      final g = newGame();
      final c = GameView(g.state, g.me.id).herd.first;
      expect(g.dispatch(RenameCamel(g.me.id, c.id, '  الغالية ')).ok, isTrue);
      expect(GameView(g.state, g.me.id).camel(c.id)!.name, 'الغالية');
      expect(
        (g.dispatch(RenameCamel(g.me.id, c.id, '')) as Err).error.code,
        ErrorCode.invalidName,
      );

      expect(g.dispatch(SetFeedPlan(g.me.id, FeedPlan.premium)).ok, isTrue);
      expect(g.me.farm.feedPlan, FeedPlan.premium);

      // a shepherd needs his caravan first; none (the player tends the herd)
      // is allowed
      expect(
        (g.dispatch(SetShepherds(g.me.id, 3)) as Err).error.code,
        ErrorCode.needsFacility,
      );
      expect(g.dispatch(SetShepherds(g.me.id, 0)).ok, isTrue);
      expect(
        (g.dispatch(SetShepherds(g.me.id, -1)) as Err).error.code,
        ErrorCode.invalidAmount,
      );

      final cash = g.me.cash;
      expect(g.dispatch(BuildFacility(g.me.id, Facility.pen)).ok, isTrue);
      expect(g.me.cash, cash - const Riyal(12000));
      g.advanceDays(Balance.buildDays);
      expect(g.me.farm.capacity, Balance.startingCapacity + 10);
      // the caravan costs more than is left
      expect(
        (g.dispatch(
          BuildFacility(g.me.id, Facility.caravan),
        ) as Err).error.code,
        ErrorCode.insufficientFunds,
      );
      expectClean(g);
    });

    test('a better feed plan raises body condition over weeks', () {
      final cheap = stocked(newGame(8));
      final rich = stocked(newGame(8));
      cheap.dispatch(SetFeedPlan(cheap.me.id, FeedPlan.economy));
      rich.dispatch(SetFeedPlan(rich.me.id, FeedPlan.premium));
      cheap.advanceDays(90);
      rich.advanceDays(90);
      double avg(Game g) {
        final h = GameView(g.state, g.me.id).herd;
        return h.map((c) => c.condition).reduce((a, b) => a + b) / h.length;
      }

      expect(avg(rich), greaterThan(avg(cheap) + 15));
    });

    test('commands about camels you do not own are refused', () {
      final g = newGame();
      final theirs = GameView(g.state, g.me.id).market.first.camel.id;
      for (final cmd in <Command>[
        Treat(g.me.id, theirs),
        RenameCamel(g.me.id, theirs, 'x'),
        ListForSale(g.me.id, theirs, 5000),
        QuickSale(g.me.id, theirs),
      ]) {
        final r = g.dispatch(cmd) as Err;
        expect(r.error.code, ErrorCode.notYourCamel, reason: '$cmd');
      }
    });
  });

  group('Own bull and withdrawal', () {
    test('mating with your own bull costs nothing but needs a mature bull', () {
      final g = stocked(newGame(13))..advanceDays(45);
      final sim = Sim(g.state);
      final bull = WorldGen(sim).makeCamel(
        sim.rng(['own-bull']),
        owner: g.me.id,
        mean: 60,
        category: ColorCategory.majaheem,
        sex: Sex.male,
        ageDays: 9 * 365,
      );
      final young = WorldGen(sim).makeCamel(
        sim.rng(['young-bull']),
        owner: g.me.id,
        mean: 60,
        category: ColorCategory.majaheem,
        sex: Sex.male,
        ageDays: 3 * 365,
      );
      final dam =
          g.state.world.camels.values.firstWhere(
              (c) =>
                  c.ownerId == g.me.id &&
                  c.sex == Sex.female &&
                  c.ageYears(g.today) >= 6,
            )
            ..lastCalvedOn = null
            ..pregnancy = null; // (the start's camel is in calf: taken empty for the test)
      final r1 = g.dispatch(MateWithOwnBull(g.me.id, dam.id, young.id)) as Err;
      expect(r1.error.code, ErrorCode.tooYoungToBreed);
      final cash = g.me.cash;
      expect(g.dispatch(MateWithOwnBull(g.me.id, dam.id, bull.id)).ok, isTrue);
      expect(g.me.cash, cash);
      final again =
          g.dispatch(MateWithOwnBull(g.me.id, dam.id, bull.id)) as Err;
      expect(again.error.code, ErrorCode.awaitingPregnancyCheck);
    });

    test('withdrawing frees the camel for sale', () {
      final g = newGame(21);
      final f = g.state.world.festivals.values.first;
      final r = f.rounds.first;
      final c = camelFor(g, f, r);
      g.advanceTo(f.opensOn);
      g.dispatch(EnterRound(g.me.id, f.id, r.id, c.id));
      expect(
        GameView(g.state, g.me.id).canSell(c.id)?.code,
        ErrorCode.enteredInContest,
      );
      expect(g.dispatch(WithdrawEntry(g.me.id, f.id, r.id, c.id)).ok, isTrue);
      expect(GameView(g.state, g.me.id).canSell(c.id), isNull);
      final again = g.dispatch(WithdrawEntry(g.me.id, f.id, r.id, c.id)) as Err;
      expect(again.error.code, ErrorCode.notEntered);
    });
  });
  group('Hidden information', () {
    test('views never reveal floors, others\' offers or exact values', () {
      final g = newGame(5);
      final v = GameView(g.state, g.me.id);
      final theirs = v.market.first;
      expect(v.offersOn(theirs.id), isEmpty);
      expect(v.quickSalePrice(theirs.camel.id), isNull);

      // The appraisal range is not centred on the true value.
      var offCentre = 0;
      for (final l in v.market.take(20)) {
        final (lo, hi) = l.camel.estimate;
        final mid = (lo.value + hi.value) / 2;
        final value = Valuation.value(
          g.state.world.camels[l.camel.id]!,
          g.today,
        ).value;
        if ((mid - value).abs() > value * 0.01) offCentre++;
      }
      expect(offCentre, greaterThan(10));

      // Another viewer hears a different appraisal of the same camel.
      final other = GameView(g.state, const OwnerId('someone-else'));
      final c = theirs.camel.id;
      expect(other.camel(c)!.estimate, isNot(v.camel(c)!.estimate));
    });

    test('a mating is only known to the owner until it is confirmed', () {
      final g = stocked(newGame(13))..advanceDays(45);
      final dam =
          g.state.world.camels.values.firstWhere(
              (c) =>
                  c.ownerId == g.me.id &&
                  c.sex == Sex.female &&
                  c.ageYears(g.today) >= 6,
            )
            ..lastCalvedOn = null
            ..pregnancy = null; // (the start's camel is in calf: taken empty for the test)
      final stud = g.state.world.studs.values.first;
      expect(g.dispatch(MateWithStud(g.me.id, dam.id, stud.id)).ok, isTrue);
      expect(GameView(g.state, g.me.id).camel(dam.id)!.awaitingCheck, isTrue);
      final stranger = GameView(g.state, const OwnerId('someone-else'));
      expect(stranger.camel(dam.id)!.awaitingCheck, isFalse);
    });
  });
  group('Save change detection', () {
    test('every camel field that can change is in mutableFields()', () {
      // Fields fixed at birth; everything else must be tracked.
      const fixed = {
        'id',
        'sex',
        'cat',
        'born',
        'chip',
        'genes',
        'env',
        'sire',
        'dam',
        'crossbred',
      };
      final g = stocked(newGame(13))..advanceDays(45);
      final c = g.state.world.camels.values.firstWhere(
        (c) => c.ownerId == g.me.id && c.sex == Sex.female,
      );
      final stud = g.state.world.studs.values.first;
      c
        ..lastCalvedOn = null
        ..placings.add(
          Placing(
            festivalId: const FestivalId('f'),
            festivalName: 'x',
            roundId: const RoundId('r'),
            rank: 1,
            of: 2,
            day: g.today,
            tier: 1,
            prize: 1,
          ),
        );
      g.dispatch(MateWithStud(g.me.id, c.id, stud.id));
      final base = c.toJson();
      final before = c.mutableFields();
      Object? changed(Object? v) => switch (v) {
        null => 1,
        final int i => i + 1,
        final double d => d + 1,
        final bool b => !b,
        final String s => '${s}x',
        final List<Object?> l => [...l, ...l],
        final Map<String, Object?> m => {
          for (final e in m.entries) e.key: changed(e.value),
        },
        _ => v,
      };
      for (final key in base.keys) {
        if (fixed.contains(key)) continue;
        final json = Map<String, Object?>.of(base);
        json[key] = switch (key) {
          'status' => 'dead',
          'health' => 'sick',
          'illness' => 'mange',
          'owner' || 'lastPlayerOwner' => 'someone-else',
          'placings' => [
            ...base['placings']! as List<Object?>,
            ...(base['placings']! as List<Object?>),
          ],
          'pregnancy' => {
            ...(base['pregnancy']! as Map<String, Object?>),
            'conceived':
                !((base['pregnancy']! as Map<String, Object?>)['conceived']!
                    as bool),
          },
          _ => changed(base[key]),
        };
        final after = Camel.fromJson(json).mutableFields();
        expect(
          after,
          isNot(equals(before)),
          reason: 'field "$key" is not tracked',
        );
      }
    });

    test('save scalars cover everything that is not a collection', () {
      final g = newGame()..advanceDays(10);
      final full = g.state.toJson().keys.toSet();
      final scalars = g.state.scalarsToJson().keys.toSet();
      expect(scalars.union(GameState.collectionKeys), full);
      final wFull = g.state.world.toJson().keys.toSet();
      final wScalars = g.state.world.scalarsToJson().keys.toSet();
      expect(wScalars.union(WorldState.collectionKeys), wFull);
    });
  });
}
