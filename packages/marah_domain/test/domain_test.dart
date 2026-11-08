import 'dart:convert';

import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/model/camel.dart';
import 'package:marah_domain/src/rules/genetics.dart';
import 'package:marah_domain/src/rules/judging.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:marah_domain/src/world_gen.dart';
import 'package:marah_domain/testing.dart';
import 'package:test/test.dart';

Game newGame([int seed = 42]) => Game.create(
  seed: seed,
  playerName: 'بدر',
  farmName: 'عزبة الصفوة',
  region: Region.qassim,
  favourite: ColorCategory.majaheem,
);

String snapshot(Game g) => jsonEncode(g.state.toJson());

Game reload(Game g) =>
    Game(GameState.fromJson(jsonDecode(snapshot(g)) as Map<String, Object?>));

/// Adds a camel to the player's herd that fits [round] of [f] on judging day.
Camel camelFor(Game g, Festival f, ContestRound r, {double mean = 70}) {
  final sim = Sim(g.state);
  // 150 days into the round's age class on judging day.
  final ageToday = r.age.minYears * 365 + 150 - f.judgedOn.daysSince(g.today);
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

  group('Age classes', () {
    test('map completed years to Gulf names', () {
      expect(AgeClass.fromDays(100), AgeClass.hwar);
      expect(AgeClass.fromDays(365 * 3 + 10), AgeClass.haq);
      expect(AgeClass.fromDays(365 * 4 + 10).labelFor(Sex.female), 'جذعة');
      expect(AgeClass.fromDays(365 * 12), AgeClass.mature);
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
    test('starts with a herd, a market, studs and a season', () {
      final g = newGame();
      final v = GameView(g.state, g.me.id);
      expect(v.herd, hasLength(3));
      expect(v.herd.every((c) => c.category == ColorCategory.majaheem), isTrue);
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
      final g = newGame();
      g.advanceDays(365 * 3);
      expect(g.state.journal.length, lessThanOrEqualTo(GameState.journalLimit));
      final later = g.advanceDays(31);
      expect(later.where((e) => e.type == EventType.wagesPaid), isNotEmpty);
    });
  });

  group('Market', () {
    test('buying pays ask plus transport and moves the camel', () {
      final g = newGame();
      final v = GameView(g.state, g.me.id);
      final l = v.market.firstWhere((l) => l.askPrice.value < 150000);
      final cash = g.me.cash;
      final r = g.dispatch(BuyListing(g.me.id, l.id));
      expect(r.ok, isTrue, reason: '$r');
      expect(g.me.cash, cash - l.askPrice - l.transport);
      expect(GameView(g.state, g.me.id).camel(l.camel.id)!.isMine, isTrue);
      expect(g.state.world.listings.containsKey(l.id), isFalse);
      expect(r.events.single.type, EventType.camelBought);
      expectClean(g);
    });

    test('refused without money or space', () {
      final g = newGame();
      final l = GameView(g.state, g.me.id).market.first;
      g.me.cash = const Riyal(100);
      final r = g.dispatch(BuyListing(g.me.id, l.id)) as Err;
      expect(r.error.code, ErrorCode.insufficientFunds);

      final g2 = newGame();
      g2.me.farm.capacity = 3;
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
      final price = v.quickSalePrice(c.id);
      expect(price, lessThan(c.estimate.$1 + c.estimate.$2));
      expect(g.dispatch(QuickSale(g.me.id, c.id)).ok, isTrue);
      expect(GameView(g.state, g.me.id).herd, hasLength(2));
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
      final stud = g.state.world.studs.values.first;
      final r = g.dispatch(MateWithStud(g.me.id, f.id, stud.id)) as Err;
      expect(r.error.code, ErrorCode.notBreedingSeason);
    });

    test('a stud that is not on offer cannot be used', () {
      final g = newGame()..advanceDays(45);
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
        final g = newGame(11)..advanceDays(45); // mid-November
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
        final born = events.where((e) => e.type == EventType.calfBorn);
        final lost = events.where((e) => e.type == EventType.calfLost);
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
      final placed = events.singleWhere((e) => e.type == EventType.placed);
      final rank = placed.data['rank']! as int;
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
      expect(events.any((e) => e.type == EventType.disqualifiedSick), isTrue);
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
}
