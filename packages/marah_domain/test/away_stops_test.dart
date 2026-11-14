// The stops that hand a jump back (task T15, docs/proposals/rush_and_calendar.md section 6), each on its day, once,
// and not when a standing order or the vet's contract covers it; the round's day refused; and the rules the second
// review found unguarded (the make-good, the milk, the rush's money, the vet's price, the standing water order, the
// summary's milk, a caller's lines).
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/handlers/handlers.dart' as handlers;
import 'package:marah_domain/src/rules/account.dart';
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

void give(Game g, int riyals) =>
    Sim(g.state).pay(g.me, Riyal(riyals), LedgerCategory.opening);

/// Stores that never run out (so no store's stop comes in a test of another).
void plenty(Game g) => g.me.farm
  ..storeKg = 1 << 30
  ..tankL = 1 << 30
  ..barleyKg = 1e8
  ..alfalfaKg = 1e8
  ..waterL = 1e9;

/// Jumped to [target] in legs, going on after each stop ([onStop] does what
/// the player would); the stops in order, the last the target's.
List<AwayStop> legs(
  Game g,
  GameDay target, {
  void Function(Game, AwayStop)? onStop,
  AwayPlan Function(GameDay)? plan,
}) {
  final out = <AwayStop>[];
  while (g.today < target) {
    final r = AwayRun(g, plan?.call(target) ?? AwayPlan(target));
    while (!r.done) {
      r.step();
    }
    out.add(r.stop!);
    onStop?.call(g, r.stop!);
  }
  return out;
}

Iterable<AwayStop> of(List<AwayStop> s, AwayStopKind k) =>
    s.where((x) => x.kind == k);

/// The first day [test] holds of a day's events, the days advanced plainly.
GameDay? firstDay(Game g, int days, bool Function(DomainEvent e) test) {
  for (var d = 0; d < days; d++) {
    if (g.advanceDays(1).any((e) => e.owner == g.me.id && test(e))) {
      return g.today;
    }
  }
  return null;
}

/// A farm of [n] grown camels more, plenty of everything.
Game bigFarm(int n, {int cash = 10000000}) {
  final g = newGame();
  final sim = Sim(g.state), gen = WorldGen(sim);
  for (var i = 0; i < n; i++) {
    gen.makeCamel(sim.rng(['stops', i]), owner: g.me.id, mean: 50);
  }
  g.me.farm
    ..capacity = n + 50
    ..shepherds = (n / Balance.camelsPerShepherd).ceil();
  plenty(g);
  give(g, cash);
  return g;
}

void main() {
  group('the stops', () {
    test('an illness: on the day she falls ill, once; none under the vet', () {
      final plain = bigFarm(40);
      final day = firstDay(plain, 200, (e) => e is FellSick)!;
      final g = bigFarm(40);
      final s = legs(g, g.today + day.daysSince(g.today) + 1);
      final ill = of(s, AwayStopKind.illness).toList();
      expect(ill.first.day, day);
      // every illness its own stop, never two for one camel
      expect(
        ill.map((x) => '${x.day.value}|${x.subject}').toSet().length,
        ill.length,
      );
      // under the vet's contract no illness stops it (she is treated that day)
      final v = bigFarm(40);
      v.dispatch(SignVetContract(v.me.id));
      final sv = legs(v, v.today + 200);
      expect(of(sv, AwayStopKind.illness), isEmpty);
    });

    test('a death of thirst: on its day; the store\'s stop comes first', () {
      final g = newGame();
      g.me.farm
        ..waterL = 0
        ..storeKg = 1 << 30
        ..barleyKg = 1e8
        ..alfalfaKg = 1e8;
      final plain = newGame();
      plain.me.farm
        ..waterL = 0
        ..storeKg = 1 << 30
        ..barleyKg = 1e8
        ..alfalfaKg = 1e8;
      final day = firstDay(
        plain,
        60,
        (e) => e is Died && e.cause == DeathCause.thirst,
      )!;
      final s = legs(g, g.today + 60);
      expect(s.first.kind, AwayStopKind.supply);
      expect(of(s, AwayStopKind.death).first.day, day);
    });

    test(
      'a store: three days before it is out; none with the standing order',
      () {
        final g = newGame();
        final plain = newGame();
        final day = firstDay(plain, 60, (e) => e is SupplyLow)!;
        final s = legs(g, g.today + 40);
        expect(
          s.first.kind,
          isIn([AwayStopKind.supply, AwayStopKind.registration]),
        );
        expect(of(s, AwayStopKind.supply).first.day, day);
        final w = newGame();
        w.dispatch(SetStandingOrder(w.me.id, StandingOrder.water, on: true));
        w.dispatch(SetStandingOrder(w.me.id, StandingOrder.feed, on: true));
        expect(of(legs(w, w.today + 90), AwayStopKind.supply), isEmpty);
      },
    );

    test('money: the day it first goes below zero, once', () {
      final g = bigFarm(40, cash: 0);
      g.me.farm.shepherds = 3;
      Sim(g.state)
          .pay(g.me, Riyal(-g.me.cash.value + 2000), LedgerCategory.fine);
      final s = legs(g, g.today + 70);
      final money = of(s, AwayStopKind.money).toList();
      expect(money, hasLength(1));
      expect(money.single.day.date.day, 1); // wages on the 1st
    });

    test('the account: a standing order refused at its limit stops it', () {
      final g = newGame();
      g.dispatch(SetStandingOrder(g.me.id, StandingOrder.water, on: true));
      Sim(g.state)
          .pay(g.me, Riyal(-g.me.cash.value - 50000), LedgerCategory.fine);
      g.me.onAccount = 1 << 20;
      final s = legs(g, g.today + 60);
      expect(of(s, AwayStopKind.account), isNotEmpty);
    });

    test('the account: reaching its limit by an order that went through', () {
      final g = newGame();
      final f = g.me.farm;
      g.dispatch(SetStandingOrder(g.me.id, StandingOrder.water, on: true));
      Sim(g.state)
          .pay(g.me, Riyal(-g.me.cash.value - 1000), LedgerCategory.fine);
      final n = Provisions.needs(
        g.state.world.aliveOwnedBy(g.me.id),
        f.feedPlan,
        g.today,
      );
      f
        ..waterL =
            n.water *
            3.5 // the order goes tomorrow
        ..calfShare = CalfShare.all; // (no milk money to pay the merchant back)
      final limit = Account.limit(
        g.state.world.aliveOwnedBy(g.me.id),
        g.me,
        g.today,
      );
      g.me.onAccount = limit - Balance.smallWaterLoadPrice.round();
      final run = AwayRun(g, AwayPlan(g.today + 10));
      final events = <DomainEvent>[];
      while (!run.done) {
        run.step();
      }
      events.addAll(g.state.inboxOf(g.me.id));
      expect(run.stop!.kind, AwayStopKind.account);
      expect(events.whereType<StandingOrderRefused>(), isEmpty);
      expect(g.me.onAccount, greaterThanOrEqualTo(limit));
    });

    test('an offer: on the day it comes', () {
      final g = newGame();
      plenty(g);
      final calf = g.state.world.aliveOwnedBy(g.me.id).last;
      expect(g.dispatch(ListForSale(g.me.id, calf.id, 1000)).ok, isTrue);
      final plain = Game(GameState.fromJson(g.state.toJson()));
      final day = firstDay(plain, 40, (e) => e is OfferReceived)!;
      final s = legs(g, g.today + 40);
      expect(of(s, AwayStopKind.offer).first.day, day);
    });

    test('a fine: a treatment found in his herd stops it on its day', () {
      final g = bigFarm(30, cash: 50000000);
      for (final c in g.state.world.aliveOwnedBy(g.me.id).toList()) {
        g.dispatch(Tamper(g.me.id, c.id, TamperKind.botox, 3));
        g.dispatch(ListForSale(g.me.id, c.id, 10000000));
      }
      final plain = Game(GameState.fromJson(g.state.toJson()));
      final day = firstDay(plain, 120, (e) => e is TamperingFound);
      expect(day, isNotNull);
      final s = legs(g, g.today + 120);
      // told that day: as the stop, or with the day's first stop
      final told = s.where(
        (x) =>
            x.kind == AwayStopKind.fine || x.also.contains(AwayStopKind.fine),
      );
      expect(told.first.day, day);
    });

    test('his round\'s day: the jump refused while it is told', () {
      final g = newGame();
      final me = g.me.id;
      final f = g.state.world.festivals.values.firstWhere(
        (x) => x.name == 'مزاين حائل',
      );
      final noura = g.state.world
          .aliveOwnedBy(me)
          .firstWhere((c) => c.sex == Sex.female);
      final r = f.rounds.firstWhere(
        (x) => x.kind == RoundKind.fardiJil && x.category == noura.category,
      );
      expect(g.dispatch(EnterRound(me, f.id, r.id, [noura.id])).ok, isTrue);
      plenty(g);
      g.advanceTo(r.day);
      expect(AwayRun.refusal(g, g.today + 5)?.params['reason'], 'round');
      g.tellTo(Game.minutesInDay);
      expect(AwayRun.refusal(g, g.today + 5), isNull);
    });

    test('registration: three days before it closes, only if he could enter '
        'and has not', () {
      final g = newGame();
      plenty(g);
      final hail = g.state.world.festivals.values.firstWhere(
        (x) => x.name == 'مزاين حائل',
      );
      final s = legs(g, hail.closesOn + 1);
      final reg = of(s, AwayStopKind.registration).toList();
      expect(reg.first.day, hail.closesOn - 3);
      expect(reg.first.subject, hail.id.value);
      expect(reg.where((x) => x.subject == hail.id.value), hasLength(1));
      // entered: no stop for that festival
      final e = newGame();
      plenty(e);
      final f = e.state.world.festivals[hail.id]!;
      final noura = e.state.world
          .aliveOwnedBy(e.me.id)
          .firstWhere((c) => c.sex == Sex.female);
      final r = f.rounds.firstWhere(
        (x) => x.kind == RoundKind.fardiJil && x.category == noura.category,
      );
      expect(
        e.dispatch(EnterRound(e.me.id, f.id, r.id, [noura.id])).ok,
        isTrue,
      );
      final se = legs(e, f.closesOn + 1);
      expect(
        of(
          se,
          AwayStopKind.registration,
        ).where((x) => x.subject == hail.id.value),
        isEmpty,
      );
      // nothing he could enter (no herd left): no stop at all
      final n = newGame();
      plenty(n);
      for (final c in n.state.world.aliveOwnedBy(n.me.id).toList()) {
        c.status = CamelStatus.gone;
      }
      expect(
        of(legs(n, hail.closesOn + 1), AwayStopKind.registration),
        isEmpty,
      );
    });

    test(
      'the breeding season: its first day, only with a female he can breed',
      () {
        // the start's نورة is in calf and her calf too young: no stop
        final g = newGame();
        plenty(g);
        final nov1 = GameDay.ofDate(DateTime.utc(2026, 11));
        expect(of(legs(g, nov1 + 2), AwayStopKind.breeding), isEmpty);
        // a grown, open, healthy she-camel: the stop on 1 November
        final b = bigFarm(30);
        final ready = b.state.world
            .aliveOwnedBy(b.me.id)
            .where((c) => Eligibility.femaleCanBreed(c, nov1) == null);
        expect(ready, isNotEmpty);
        final s = of(legs(b, nov1 + 2), AwayStopKind.breeding).toList();
        expect(s, hasLength(1));
        expect(s.single.day, nov1);
      },
    );

    test('the pens outgrown: on the day the herd passes their room, once', () {
      final g = newGame();
      plenty(g);
      g.me.farm.capacity = 2;
      final dam = g.state.world
          .aliveOwnedBy(g.me.id)
          .firstWhere((c) => c.sex == Sex.female);
      final due = dam.pregnancy!.dueOn;
      final s = legs(g, due + 2);
      final c = of(s, AwayStopKind.crowded).toList();
      expect(c, hasLength(1));
      expect(c.single.day, due);
    });
  });

  group('the round first (L2)', () {
    test(
      'a trip that takes the money below zero: the round told, money said',
      () {
        final g = newGame();
        final me = g.me.id;
        final f = g.state.world.festivals.values.firstWhere(
          (x) => x.name == 'مزاين حائل',
        );
        final noura = g.state.world
            .aliveOwnedBy(me)
            .firstWhere((c) => c.sex == Sex.female);
        final r = f.rounds.firstWhere(
          (x) => x.kind == RoundKind.fardiJil && x.category == noura.category,
        );
        g.dispatch(EnterRound(me, f.id, r.id, [noura.id]));
        plenty(g);
        g.advanceTo(r.day - 1);
        // a few riyals left: the trip at judging takes it below zero
        Sim(g.state)
            .pay(g.me, Riyal(-g.me.cash.value + 10), LedgerCategory.fine);
        final run = AwayRun(g, AwayPlan(r.day + 5));
        while (!run.done) {
          run.step();
        }
        expect(run.stop!.kind, AwayStopKind.round);
        expect(run.stop!.also, contains(AwayStopKind.money));
        expect(g.me.cash.isNegative, isTrue);
      },
    );
  });

  group('the rules the review found unguarded', () {
    Game shortTwice() {
      // left alone till the herd has gone two days dry
      final g = newGame();
      while (g.me.farm.dryDays < 2) {
        g.advanceDays(1);
      }
      return g;
    }

    test(
      'half a day of water keeps the earlier dry count; no thirst given back',
      () {
        final g = shortTwice();
        final f = g.me.farm, r = f.today!;
        expect(r.dryBefore, 1);
        expect(f.dryDays, 2);
        final before = {
          for (final c in g.state.world.aliveOwnedBy(g.me.id))
            c.id: c.condition,
        };
        f
          ..waterL = r.waterNeed * 0.6
          ..deliveries.add(
            Delivery(
              supply: Supply.water,
              units: 1,
              arrivesOn: g.today + 1,
              size: 0,
            ),
          );
        expect(
          g.dispatch(RushDelivery(g.me.id, StandingOrder.water)).ok,
          isTrue,
        );
        expect(f.dryDays, 1);
        for (final c in g.state.world.aliveOwnedBy(g.me.id)) {
          expect(c.condition, before[c.id]);
        }
      },
    );

    test('a short day that was no dry day: no thirst given back', () {
      final g = newGame();
      final f = g.me.farm;
      // the next dawn finds 60% of the day's water: short, but half or more
      // holds the dry count at 0
      final n = Provisions.needs(
        g.state.world.aliveOwnedBy(g.me.id),
        f.feedPlan,
        g.today + 1,
      );
      f.waterL = n.water * 0.6;
      g.advanceDays(1);
      expect(f.short.contains(Supply.water), isTrue);
      expect(f.dryDays, 0);
      final before = {
        for (final c in g.state.world.aliveOwnedBy(g.me.id)) c.id: c.condition,
      };
      g.dispatch(
        OrderSupply(g.me.id, Supply.water, 1, tanker: Tanker.small, now: true),
      );
      expect(f.short.contains(Supply.water), isFalse);
      for (final c in g.state.world.aliveOwnedBy(g.me.id)) {
        expect(c.condition, before[c.id]);
      }
    });

    test('the milk view stands after a feed rush', () {
      final g = newGame();
      while (g.me.farm.fedShare >= 1) {
        g.advanceDays(1);
      }
      final me = g.me.id, f = g.me.farm;
      final litres = Milk.today(
        g.state.world,
        me,
        f,
        g.today,
      ).map((m) => m.litres).toList();
      g.dispatch(OrderSupply(me, Supply.barley, 4));
      g.dispatch(OrderSupply(me, Supply.alfalfa, 8));
      expect(g.dispatch(RushDelivery(me, StandingOrder.feed)).ok, isTrue);
      expect(f.fedShare, greaterThan(f.today!.fedAtDawn));
      expect(
        Milk.today(g.state.world, me, f, g.today).map((m) => m.litres),
        litres,
      );
    });

    test('a delivery rush is paid from cash only', () {
      final g = newGame();
      while (!g.me.farm.short.contains(Supply.water)) {
        g.advanceDays(1);
      }
      final me = g.me.id;
      g.dispatch(OrderSupply(me, Supply.water, 1, tanker: Tanker.small));
      Sim(g.state).pay(g.me, Riyal(-g.me.cash.value + 10), LedgerCategory.fine);
      final owed = g.me.onAccount;
      final r = g.dispatch(RushDelivery(me, StandingOrder.water));
      expect((r as Err).error.code, ErrorCode.insufficientFunds);
      expect(g.me.onAccount, owed);
      expect(g.me.farm.deliveries, isNotEmpty);
    });

    test('a feed rush costs half the order, at most 300', () {
      final g = newGame();
      while (g.me.farm.fedShare >= 1) {
        g.advanceDays(1);
      }
      final me = g.me.id;
      g.me.farm.storeKg = 1 << 20;
      give(g, 100000);
      g.dispatch(OrderSupply(me, Supply.barley, 2));
      final small = g.dispatch(RushDelivery(me, StandingOrder.feed));
      final fee1 = small.events.whereType<Rushed>().single.fee;
      expect(
        fee1,
        (2 * Provisions.unitPrice(Supply.barley, g.me.farm.region) * 0.5)
            .round(),
      );
      // a big order the next short day: capped
      final h = newGame();
      while (h.me.farm.fedShare >= 1) {
        h.advanceDays(1);
      }
      h.me.farm.storeKg = 1 << 20;
      give(h, 100000);
      h.dispatch(OrderSupply(h.me.id, Supply.barley, 40));
      final big = h.dispatch(RushDelivery(h.me.id, StandingOrder.feed));
      expect(big.events.whereType<Rushed>().single.fee, Balance.rushFeedCap);
    });

    test('the vet\'s price holds while each is sick, for every camel', () {
      final g = bigFarm(12);
      final sim = Sim(g.state);
      final sick = g.state.world.aliveOwnedBy(g.me.id).take(8).toList();
      for (final c in sick) {
        c
          ..health = HealthStatus.sick
          ..illness = Illness.pneumonia
          ..sickSince = g.today;
      }
      final first = {for (final c in sick) c.id: handlers.vetQuote(sim, c)};
      for (var d = 0; d < 4; d++) {
        g.advanceDays(1);
        for (final c in sick.where((c) => c.health == HealthStatus.sick)) {
          expect(
            handlers.vetQuote(Sim(g.state), c),
            first[c.id],
            reason: '${c.name} day $d',
          );
        }
      }
    });

    test(
      'a herd that drinks more than a tanker a day: several sent at once',
      () {
        final g = bigFarm(1200);
        final f = g.me.farm;
        final n = Provisions.needs(
          g.state.world.aliveOwnedBy(g.me.id),
          f.feedPlan,
          g.today,
        );
        expect(n.water, greaterThan(Balance.waterLoadL));
        f
          ..tankL = (n.water * 10).round()
          ..waterL = n.water * 5;
        g.dispatch(SetStandingOrder(g.me.id, StandingOrder.water, on: true));
        final sent = <SupplyOrdered>[];
        for (var d = 0; d < 20; d++) {
          sent.addAll(g.advanceDays(1).whereType<SupplyOrdered>());
          expect(f.dryDays, 0, reason: 'day $d');
        }
        expect(sent.any((e) => e.units > 1), isTrue);
      },
    );

    test('the summary counts the milk', () {
      final g = newGame();
      plenty(g);
      int milk() => g.me.ledger
          .where((e) => e.category == LedgerCategory.milk)
          .fold(0, (n, e) => n + e.amount.value);
      final before = milk();
      final run = AwayRun(g, AwayPlan(g.today + 5));
      while (!run.done) {
        run.step();
      }
      expect(run.summary.milk, greaterThan(0));
      expect(run.summary.milk, milk() - before);
    });

    test('the make-good leaves alone a camel that came today (L1)', () {
      final g = newGame();
      while (!g.me.farm.short.contains(Supply.water)) {
        g.advanceDays(1);
      }
      final me = g.me.id;
      give(g, 100000);
      final l = g.state.world.listings.values.toList()
        ..sort((a, b) => a.askPrice.value - b.askPrice.value);
      expect(
        g.dispatch(BuyListing(me, l.first.id, now: true, hour: 0)).ok,
        isTrue,
      );
      final c = g.state.world.camels[l.first.camelId]!;
      final was = c.condition;
      expect(
        g
            .dispatch(
              OrderSupply(me, Supply.water, 1, tanker: Tanker.small, now: true),
            )
            .ok,
        isTrue,
      );
      expect(c.condition, was);
    });

    test(
      'a caller\'s own lines: counted into the summary, the card carried (L3)',
      () {
        final g = newGame();
        plenty(g);
        final run = AwayRun(
          g,
          AwayPlan(
            g.today + 4,
            counters: [
              (game, events, s) =>
                  s.extra['days out'] = (s.extra['days out'] ?? 0) + 1,
            ],
            card: const {'gear': 'شبك وحمام'},
          ),
        );
        while (!run.done) {
          run.step();
        }
        expect(run.summary.extra['days out'], run.summary.days);
        expect(run.toJson()['card'], {'gear': 'شبك وحمام'});
        expect((run.toJson()['summary']! as Map)['extra'], {
          'days out': run.summary.days,
        });
      },
    );
  });
}
