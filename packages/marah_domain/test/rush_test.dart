// The rush, the standing order and the vet's contract (task T15, part B;
// docs/proposals/rush_and_calendar.md sections 2, 6 and 7).
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/persistence.dart';
import 'package:marah_domain/src/handlers/handlers.dart' as handlers;
import 'package:marah_domain/src/rules/eligibility.dart';
import 'package:marah_domain/src/rules/milk.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:marah_domain/src/world_gen.dart';
import 'package:test/test.dart';

Game newGame() => Game.create(
  seed: 4242,
  playerName: 'p',
  farmName: 'f',
  region: Region.qassim,
  favourite: ColorCategory.wodh,
  startedAt: DateTime.utc(2026, 11, 14),
);

/// A copy through the save's own JSON (a game played two ways from here).
Game copyOf(Game g) => Game(GameState.fromJson(g.state.toJson()));

/// Left alone till the herd went short of water and feed (1 November).
Game shortDay() {
  final g = newGame();
  while (!(g.me.farm.short.contains(Supply.water) &&
      g.me.farm.short.length == 3)) {
    g.advanceDays(1);
  }
  return g;
}

void give(Game g, int riyals) =>
    Sim(g.state).pay(g.me, Riyal(riyals), LedgerCategory.opening);

int rushRows(Game g) => g.me.ledger
    .where((e) => e.category == LedgerCategory.rush)
    .fold(0, (n, e) => n - e.amount.value);

void main() {
  group('a facility', () {
    test(
      'rushed while building: stands now, half its price for three days',
      () {
        final g = newGame();
        final me = g.me.id;
        expect(g.dispatch(BuildFacility(me, Facility.pen)).ok, isTrue);
        final cash = g.me.cash.value;
        final r = g.dispatch(RushBuild(me, Facility.pen));
        expect(r.ok, isTrue, reason: '$r');
        expect(g.me.farm.has(Facility.pen), 1);
        expect(g.me.farm.building, isEmpty);
        expect(g.me.farm.capacity, Balance.startingCapacity + 10);
        expect(cash - g.me.cash.value, 6000);
        expect(rushRows(g), 6000);
        expect(r.events.whereType<FacilityBuilt>(), hasLength(1));
        expect(r.events.whereType<Rushed>().single.fee, 6000);
        // nothing left to hurry
        expect(g.dispatch(RushBuild(me, Facility.pen)).ok, isFalse);
      },
    );

    test('the price falls with the days left', () {
      final g = newGame();
      g.dispatch(BuildFacility(g.me.id, Facility.pen));
      g.advanceDays(2);
      expect(
        g
            .dispatch(RushBuild(g.me.id, Facility.pen))
            .events
            .whereType<Rushed>()
            .single
            .fee,
        2000,
      );
    });

    test('at ordering: price and rush together, refused when short', () {
      final g = newGame();
      final me = g.me.id;
      // 20,000: the pen's 12,000 and 6,000 more fit; the tent's 15,000 and
      // 7,500 do not, and nothing is ordered
      final no = g.dispatch(BuildFacility(me, Facility.tent, now: true));
      expect(no.ok, isFalse);
      expect((no as Err).error.code, ErrorCode.insufficientFunds);
      expect(g.me.farm.building, isEmpty);
      expect(g.me.cash.value, 20000);
      final r = g.dispatch(BuildFacility(me, Facility.pen, now: true));
      expect(r.ok, isTrue);
      expect(g.me.farm.has(Facility.pen), 1);
      expect(g.me.cash.value, 2000);
    });

    test('cash only: refused below zero, never on the account', () {
      final g = newGame();
      g.dispatch(BuildFacility(g.me.id, Facility.pen));
      Sim(g.state).pay(g.me, Riyal(-g.me.cash.value - 10), LedgerCategory.fine);
      final r = g.dispatch(RushBuild(g.me.id, Facility.pen));
      expect((r as Err).error.code, ErrorCode.inDebt);
      expect(g.me.onAccount, 0);
    });
  });

  group('water and feed', () {
    test('not offered on an ordinary day', () {
      final g = newGame();
      final me = g.me.id;
      g.dispatch(OrderSupply(me, Supply.water, 1, tanker: Tanker.small));
      final r = g.dispatch(RushDelivery(me, StandingOrder.water));
      expect((r as Err).error.code, ErrorCode.notShortToday);
      final at = g.dispatch(
        OrderSupply(me, Supply.water, 1, tanker: Tanker.small, now: true),
      );
      expect((at as Err).error.code, ErrorCode.notShortToday);
    });

    test('on a short day the tanker makes the day full: no longer dry', () {
      final g = shortDay();
      final me = g.me.id, f = g.me.farm;
      expect(f.dryDays, 1);
      final dawn = {
        for (final c in g.state.world.aliveOwnedBy(me)) c.id: c.condition,
      };
      final milkMoney = g.me.ledger
          .where((e) => e.category == LedgerCategory.milk)
          .last
          .amount;
      final litres = Milk.today(
        g.state.world,
        me,
        f,
        g.today,
      ).map((m) => m.litres).toList();
      expect(
        g.dispatch(OrderSupply(me, Supply.water, 1, tanker: Tanker.small)).ok,
        isTrue,
      );
      final cash = g.me.cash.value;
      final r = g.dispatch(RushDelivery(me, StandingOrder.water));
      expect(r.ok, isTrue, reason: '$r');
      expect(cash - g.me.cash.value, 60);
      expect(f.dryDays, 0);
      expect(f.short.contains(Supply.water), isFalse);
      expect(f.deliveries.where((d) => d.supply == Supply.water), isEmpty);
      expect(f.today!.waterDrunk, closeTo(f.today!.waterNeed, 1e-9));
      // today's condition: what Care would have made of the day without its
      // thirst (exact up to Care's rounding and clamp)
      for (final c in g.state.world.aliveOwnedBy(me)) {
        expect(
          c.condition,
          closeTo(
            dawn[c.id]! + Balance.conditionPull * Balance.thirstPenalty,
            0.011,
          ),
        );
      }
      // the milk stands: the view's litres and the ledger's money
      expect(
        Milk.today(g.state.world, me, f, g.today).map((m) => m.litres),
        litres,
      );
      expect(
        g.me.ledger.where((e) => e.category == LedgerCategory.milk).last.amount,
        milkMoney,
      );
      // tomorrow is no dry day
      g.advanceDays(1);
      expect(f.dryDays, 0);
    });

    test(
      'half a day holds the count; under half changes nothing but litres',
      () {
        for (final (litres, expectDry) in [(0.6, 1), (0.3, 1)]) {
          final g = shortDay();
          final me = g.me.id, f = g.me.farm;
          final r0 = f.today!;
          // the tank holds only the part: the rush brings what fits (a tank
          // nearly full), tested on the record directly
          final need = r0.waterNeed;
          f
            ..waterL = need * litres
            ..deliveries.clear();
          f.deliveries.add(
            Delivery(
              supply: Supply.water,
              units: 1,
              arrivesOn: g.today + 1,
              size: 0,
            ),
          );
          final ok = g.dispatch(RushDelivery(me, StandingOrder.water));
          expect(ok.ok, isTrue, reason: '$ok');
          expect(f.dryDays, litres >= 0.5 ? r0.dryBefore : expectDry);
          expect(f.short.contains(Supply.water), isTrue);
        }
      },
    );

    test('feed on a short day: the ration made up, fed again', () {
      final g = shortDay();
      final me = g.me.id, f = g.me.farm;
      expect(f.fedShare, lessThan(1));
      final dawn = {
        for (final c in g.state.world.aliveOwnedBy(me)) c.id: c.condition,
      };
      final before = f.fedShare;
      final r = g.dispatch(OrderSupply(me, Supply.barley, 2, now: true));
      expect(r.ok, isTrue, reason: '$r');
      final r2 = g.dispatch(OrderSupply(me, Supply.alfalfa, 4));
      expect(r2.ok, isTrue);
      final r3 = g.dispatch(RushDelivery(me, StandingOrder.feed));
      expect(r3.ok, isTrue, reason: '$r3');
      expect(f.fedShare, 1);
      expect(f.short, {Supply.water});
      final gain =
          Balance.conditionPull *
          (f.feedPlan.conditionTarget - 35) *
          (1 - before);
      for (final c in g.state.world.aliveOwnedBy(me)) {
        expect(c.condition, closeTo(dawn[c.id]! + gain, 0.03));
      }
      // the fee: half the order again, at most 300
      final fees = g.me.ledger
          .where((e) => e.category == LedgerCategory.rush)
          .map((e) => -e.amount.value)
          .toList();
      expect(fees.every((x) => x <= Balance.rushFeedCap), isTrue);
    });

    test('nothing is gained by running short and rushing', () {
      // the same day reached two ways: water ordered in time the day before,
      // or let run out and rushed
      final short = shortDay();
      final day = short.today;
      final inTime = newGame();
      while (inTime.today < day - 1) {
        inTime.advanceDays(1);
      }
      inTime.dispatch(
        OrderSupply(inTime.me.id, Supply.water, 1, tanker: Tanker.small),
      );
      inTime.dispatch(OrderSupply(inTime.me.id, Supply.barley, 2));
      inTime.dispatch(OrderSupply(inTime.me.id, Supply.alfalfa, 8));
      inTime.advanceDays(1);
      final me = short.me.id;
      short.dispatch(
        OrderSupply(me, Supply.water, 1, tanker: Tanker.small, now: true),
      );
      short.dispatch(OrderSupply(me, Supply.barley, 2, now: true));
      short.dispatch(OrderSupply(me, Supply.alfalfa, 8));
      short.dispatch(RushDelivery(me, StandingOrder.feed));
      expect(short.me.cash.value, lessThan(inTime.me.cash.value));
      final a = {
        for (final c in inTime.state.world.aliveOwnedBy(inTime.me.id))
          c.id: c.condition,
      };
      for (final c in short.state.world.aliveOwnedBy(me)) {
        expect(c.condition, lessThanOrEqualTo(a[c.id]! + 0.01));
      }
    });
  });

  group('the truck', () {
    Listing cheapest(Game g) {
      final ls = g.state.world.listings.values.toList()
        ..sort((a, b) => a.askPrice.value - b.askPrice.value);
      return ls.first;
    }

    test('priced by the hour, acquiredOn unchanged, arrived now', () {
      final g = newGame();
      final me = g.me.id, l = cheapest(g);
      final trucking = handlers.transportToFarm(g.me, l);
      expect(g.dispatch(BuyListing(me, l.id)).ok, isTrue);
      final c = g.state.world.camels[l.camelId]!;
      expect(Eligibility.onTheWay(c, g.today), isTrue);
      final cash = g.me.cash.value;
      final r = g.dispatch(RushTruck(me, c.id, hour: 18));
      expect(r.ok, isTrue);
      expect(cash - g.me.cash.value, Balance.rushTruckFee(trucking, 18));
      expect(Balance.rushTruckFee(1069, 0), 535);
      expect(Balance.rushTruckFee(1069, 18), 135);
      expect(Balance.rushTruckFee(1069, 23), 105);
      expect(c.acquiredOn, g.today);
      expect(c.arrivedOn, g.today);
      expect(Eligibility.onTheWay(c, g.today), isFalse);
      // milked and sellable today; the 30 days of ownership unchanged
      expect(Eligibility.canSell(g.state.world, c, me), isNull);
      expect(g.today.daysSince(c.acquiredOn), 0);
    });

    test('at buying: bought and brought now', () {
      final g = newGame();
      final l = cheapest(g);
      final r = g.dispatch(BuyListing(g.me.id, l.id, now: true, hour: 0));
      expect(r.ok, isTrue, reason: '$r');
      final c = g.state.world.camels[l.camelId]!;
      expect(c.arrivedOn, g.today);
      expect(r.events.whereType<Rushed>(), hasLength(1));
    });

    test('a purchase clears arrivedOn', () {
      final g = newGame();
      final l = cheapest(g);
      final c = g.state.world.camels[l.camelId]!..arrivedOn = g.today - 50;
      g.dispatch(BuyListing(g.me.id, l.id));
      expect(c.arrivedOn, isNull);
      expect(Eligibility.onTheWay(c, g.today), isTrue);
    });
  });

  group('the standing order', () {
    test('a top-up sent when a store comes to 3 days, paid as an order', () {
      final g = newGame();
      final me = g.me.id;
      g.dispatch(SetStandingOrder(me, StandingOrder.water, on: true));
      g.dispatch(SetStandingOrder(me, StandingOrder.feed, on: true));
      final sent = <SupplyOrdered>[];
      for (var d = 0; d < 60; d++) {
        sent.addAll(g.advanceDays(1).whereType<SupplyOrdered>());
      }
      expect(sent, isNotEmpty);
      expect(sent.every((e) => e.standing), isTrue);
      expect(g.me.farm.dryDays, 0);
      expect(g.me.farm.short, isEmpty);
      expect(
        g.me.ledger.any((e) => e.category == LedgerCategory.water),
        isTrue,
      );
    });

    test('a large herd: as many tankers as the tank takes, never dry', () {
      final g = newGame();
      final sim = Sim(g.state), gen = WorldGen(sim), f = g.me.farm;
      for (var i = 0; i < 300; i++) {
        gen.makeCamel(sim.rng(['big', i]), owner: g.me.id, mean: 50);
      }
      final n = Provisions.needs(sim.herdOf(g.me.id), f.feedPlan, g.today);
      f
        ..capacity = 400
        ..shepherds = 12
        ..tankL = (n.water * 20).round()
        ..storeKg = ((n.barley + n.alfalfa) * 20).round()
        ..waterL = n.water * 10
        ..barleyKg = n.barley * 10
        ..alfalfaKg = n.alfalfa * 10;
      give(g, 5000000);
      g.dispatch(SetStandingOrder(g.me.id, StandingOrder.water, on: true));
      g.dispatch(SetStandingOrder(g.me.id, StandingOrder.feed, on: true));
      for (var d = 0; d < 90; d++) {
        g.advanceDays(1);
        expect(f.dryDays, 0, reason: 'day $d');
        expect(f.short, isEmpty, reason: 'day $d');
      }
    });

    test('refused at the account limit: said, nothing sent', () {
      final g = newGame();
      final me = g.me.id;
      g.dispatch(SetStandingOrder(me, StandingOrder.water, on: true));
      Sim(g.state)
          .pay(g.me, Riyal(-g.me.cash.value - 50000), LedgerCategory.fine);
      g.me.onAccount = 1 << 20;
      final refused = <StandingOrderRefused>[];
      for (var d = 0; d < 40; d++) {
        refused.addAll(g.advanceDays(1).whereType<StandingOrderRefused>());
      }
      expect(refused, isNotEmpty);
    });
  });

  group('the vet', () {
    Camel makeSick(Game g) {
      final c = g.state.world.aliveOwnedBy(g.me.id).first
        ..health = HealthStatus.sick
        ..illness = Illness.mange
        ..sickSince = g.today;
      return c;
    }

    test('the price holds while she is sick (keyed by the illness)', () {
      final g = newGame();
      final c = makeSick(g);
      final a = handlers.vetQuote(Sim(g.state), c);
      g.advanceDays(1);
      c
        ..health = HealthStatus.sick
        ..illness = Illness.mange;
      expect(handlers.vetQuote(Sim(g.state), c), a);
      final r = g.dispatch(Treat(g.me.id, c.id));
      expect(r.events.whereType<Treated>().single.cost, a.value);
    });

    test('the contract: billed for the rest of the month, cash only', () {
      final g = newGame(); // 1 October
      final me = g.me.id;
      final fee = Balance.vetContractFee(2);
      final cash = g.me.cash.value;
      final r = g.dispatch(SignVetContract(me));
      expect(r.ok, isTrue);
      expect(cash - g.me.cash.value, fee); // the whole of October
      expect(g.dispatch(SignVetContract(me)).ok, isFalse);
      // the 1st of November: the month's fee
      final c2 = g.me.cash.value;
      do {
        g.advanceDays(1);
      } while (g.today.date.day != 1);
      expect(
        g.me.ledger.where((e) => e.category == LedgerCategory.vetContract),
        hasLength(2),
      );
      expect(c2, greaterThan(g.me.cash.value));
    });

    test('signing short of cash is refused, the account untouched', () {
      final g = newGame();
      Sim(g.state)
          .pay(g.me, Riyal(-g.me.cash.value + 100), LedgerCategory.fine);
      final r = g.dispatch(SignVetContract(g.me.id));
      expect((r as Err).error.code, ErrorCode.insufficientFunds);
      expect(g.me.farm.vet, isNull);
      expect(g.me.onAccount, 0);
    });

    test(
      'signing treats every camel sick now; later ones the day they fall ill',
      () {
        final g = newGame();
        final c = makeSick(g);
        final r = g.dispatch(SignVetContract(g.me.id));
        expect(r.events.whereType<Treated>().single.camel, c.id);
        expect(c.health, HealthStatus.treated);
        // a long run: every illness treated the day it comes
        final calf = g.state.world.aliveOwnedBy(g.me.id).last;
        for (var d = 0; d < 400; d++) {
          for (final e in g.advanceDays(1)) {
            if (e is FellSick && e.owner == g.me.id) {
              final x = g.state.world.camels[e.camel!]!;
              expect(x.health, HealthStatus.treated, reason: x.name);
            }
          }
          g.me.farm
            ..barleyKg = 1e5
            ..alfalfaKg = 1e5
            ..waterL = 1e5;
          g.me.farm.storeKg = 1 << 20;
          g.me.farm.tankL = 1 << 20;
        }
        expect(calf, isNotNull);
      },
    );

    test('at the account limit the contract cannot treat: said', () {
      final g = newGame();
      g.dispatch(SignVetContract(g.me.id));
      Sim(g.state).pay(g.me, Riyal(-g.me.cash.value), LedgerCategory.fine);
      g.me.onAccount = 1 << 20;
      final s = Sim(g.state);
      final c = makeSick(g);
      final r = handlers.treatCamel(s, g.me, c);
      expect(r.ok, isFalse);
    });

    test('cancelled: runs to the month end, then ends', () {
      final g = newGame();
      g.dispatch(SignVetContract(g.me.id));
      final r = g.dispatch(CancelVetContract(g.me.id));
      expect(r.ok, isTrue);
      expect(g.me.farm.vet!.endsOn, GameDay.ofDate(DateTime.utc(2026, 10, 31)));
      do {
        g.advanceDays(1);
      } while (g.today.date.day != 1);
      expect(g.me.farm.vet, isNull);
      expect(
        g.me.ledger.where((e) => e.category == LedgerCategory.vetContract),
        hasLength(1),
      );
    });
  });

  group('treat all', () {
    /// [n] of a big herd sick, each falling ill a day apart (the oldest
    /// first by day), the vet's quote of each.
    (Game, List<Camel>) sickHerd(int n) {
      final g = newGame();
      final sim = Sim(g.state), gen = WorldGen(sim);
      for (var i = 0; i < n; i++) {
        gen.makeCamel(sim.rng(['ta', i]), owner: g.me.id, mean: 50);
      }
      g.me.farm.capacity = n + 10;
      final sick = g.state.world.aliveOwnedBy(g.me.id).take(n).toList();
      for (var i = 0; i < n; i++) {
        // the newest first in the herd's own order: the treatment must sort
        sick[i]
          ..health = HealthStatus.sick
          ..illness = Illness.mange
          ..sickSince = g.today - i;
      }
      return (g, sick);
    }

    test('the oldest illness first; the total is the quotes\' sum and what is charged', () {
      final (g, sick) = sickHerd(6);
      give(g, 1000000);
      final sim = Sim(g.state);
      final quotes = {
        for (final c in sick) c.id: handlers.vetQuote(sim, c).value,
      };
      final total = quotes.values.fold(0, (a, b) => a + b);
      expect(rushFacts(g.state, g.me.id)['treatAll'], total);
      final cash = g.me.cash.value;
      final r = g.dispatch(TreatAll(g.me.id));
      expect(r.ok, isTrue);
      final treated = r.events.whereType<Treated>().toList();
      // the oldest illness first: sickSince ascending
      final order = [
        for (final t in treated)
          g.state.world.camels[t.camel!]!.sickSince!.value,
      ];
      expect(order, [...order]..sort());
      expect(order.length, 6);
      expect(cash - g.me.cash.value, total);
      expect([for (final t in treated) t.cost].fold(0, (a, b) => a + b), total);
    });

    test('stops at the first refusal at the account\'s limit', () {
      final (g, sick) = sickHerd(6);
      // no cash; the account takes about two treatments more
      Sim(g.state).pay(g.me, Riyal(-g.me.cash.value), LedgerCategory.fine);
      final limit = handlers.accountLimit(Sim(g.state), g.me);
      final oldest = [...sick]
        ..sort((a, b) => a.sickSince!.value - b.sickSince!.value);
      // the third dear (pneumonia: 600 to 1,800), the fourth cheap (a calf's
      // diarrhoea: 150 to 400): room after the first two for the fourth but
      // not the third, so going on past the refusal would treat the fourth
      oldest[2].illness = Illness.pneumonia;
      oldest[3].illness = Illness.calfDiarrhea;
      final q = [
        for (final c in oldest) handlers.vetQuote(Sim(g.state), c).value,
      ];
      expect(q[2], greaterThan(450));
      expect(q[3], lessThanOrEqualTo(450));
      g.me.onAccount = limit - q[0] - q[1] - 450;
      final r = g.dispatch(TreatAll(g.me.id));
      expect(r.ok, isTrue);
      final treated = r.events
          .whereType<Treated>()
          .map((e) => e.camel)
          .toList();
      expect(treated, [oldest[0].id, oldest[1].id]);
      expect(oldest[2].health, HealthStatus.sick);
      expect(oldest.last.health, HealthStatus.sick);
      expect(g.me.onAccount, limit - 450);
      expect(oldest[3].health, HealthStatus.sick);
    });
  });

  test('an AwayRun to a day equals the days advanced (VM and JavaScript)', () {
    Game scripted() {
      final g = newGame();
      final me = g.me.id;
      g.dispatch(SetStandingOrder(me, StandingOrder.water, on: true));
      g.dispatch(SetStandingOrder(me, StandingOrder.feed, on: true));
      g.dispatch(SignVetContract(me));
      g.dispatch(BuildFacility(me, Facility.pen));
      return g;
    }

    final a = scripted()..advanceDays(200);
    final b = scripted();
    final target = b.today + 200;
    final kinds = <AwayStopKind>[];
    while (b.today < target) {
      final run = AwayRun(b, AwayPlan(target));
      while (!run.done) {
        run.step();
      }
      kinds.add(run.stop!.kind);
    }
    expect(kinds.last, AwayStopKind.target);
    expect(b.state.toJson(), a.state.toJson());
  });

  test('the new state survives the save', () {
    final g = shortDay();
    final me = g.me.id;
    g.dispatch(SetStandingOrder(me, StandingOrder.feed, on: true));
    g.dispatch(SignVetContract(me));
    final l = g.state.world.listings.values.first;
    give(g, 100000);
    g.dispatch(BuyListing(me, l.id, now: true, hour: 3));
    final back = copyOf(g);
    expect(back.me.farm.standing, {StandingOrder.feed});
    expect(back.me.farm.vet!.since, g.today);
    expect(back.me.farm.today!.waterNeed, g.me.farm.today!.waterNeed);
    expect(back.state.world.camels[l.camelId]!.arrivedOn, g.today);
    expect(checkInvariants(back.state), isEmpty);
    // (WorldGen is imported for the long runs' helpers)
    expect(WorldGen, isNotNull);
  });
}
