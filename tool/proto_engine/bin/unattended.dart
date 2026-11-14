// What happens when days pass and nobody tends the farm (task T15, the calendar's design:
// docs/proposals/rush_and_calendar.md), by the engine's own rules: a game left alone for a week, a season (91 days)
// and a year, and what each stretch brought, by the engine's events. A measurement, not the game.
//
//   dart run tool/proto_engine/bin/unattended.dart          (the farms left alone)
//   dart run tool/proto_engine/bin/unattended.dart stops    (a jump with the design's stops: how often it stops)
//
// Farms (seed 4242, the game's start on 1 October 2026):
//  - start:  the new game as it is (one nursing she-camel, her calf, SAR 20,000, a month of feed and water);
//  - full:   the farm built out (five more pens, the 30,000 L tank, the store, the caravan), 56 head, three
//            shepherds, the tank and the store filled to the top on the first day;
//  - full, kept stocked: the same with the tank and the store topped up each morning (what a standing order would
//            do), with and without every camel that falls ill treated the day she does (what a vet's contract
//            would do): what the illnesses alone cost a herd left alone.
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/rules/account.dart';
import 'package:marah_domain/src/rules/eligibility.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:marah_domain/src/world_gen.dart';

Game start() => Game.create(
  seed: 4242,
  playerName: 'away',
  farmName: 'away',
  region: Region.qassim,
  favourite: ColorCategory.wodh,
  startedAt: DateTime.utc(2026, 11, 14),
);

Game full() {
  final g = start();
  final f = g.me.farm;
  for (final x in Facility.values) {
    f.built[x] = x.most;
  }
  f
    ..capacity = Balance.startingCapacity + 5 * Facility.pen.head
    ..tankL = Balance.startingTankL + Facility.tank.litres
    ..storeKg = Balance.startingStoreKg + Facility.store.kg
    ..shepherds = 3;
  final sim = Sim(g.state);
  final gen = WorldGen(sim);
  for (var i = 0; i < 54; i++) {
    gen.makeCamel(sim.rng(['full', i]), owner: g.me.id, mean: 50);
  }
  // the store filled with the ration's own mix, the tank to the top
  final n = Provisions.needs(sim.herdOf(g.me.id), f.feedPlan, g.today);
  final share = n.barley / (n.barley + n.alfalfa);
  f
    ..barleyKg = f.storeKg * share
    ..alfalfaKg = f.storeKg * (1 - share)
    ..waterL = f.tankL.toDouble();
  return g;
}

void run(
  String name,
  Game Function() make,
  int span, {
  bool vet = false,
  bool topUp = false,
}) {
  final g = make();
  final me = g.me.id;
  final cash0 = g.me.cash.value;
  final head0 = g.state.world.aliveOwnedBy(me).length;
  final first = <String, int>{};
  final counts = <String, int>{};
  final deaths = <String, int>{};
  for (var d = 1; d <= span; d++) {
    if (topUp) {
      // the tank and the store kept full, as a standing order would
      final f = g.me.farm;
      final share = f.barleyKg + f.alfalfaKg <= 0
          ? 0.3
          : f.barleyKg / (f.barleyKg + f.alfalfaKg);
      f
        ..barleyKg = f.storeKg * share
        ..alfalfaKg = f.storeKg * (1 - share)
        ..waterL = f.tankL.toDouble();
    }
    for (final e in g.advanceDays(1)) {
      if (e.owner != null && e.owner != me) continue;
      final t = e is SupplyLow
          ? '${e.type}:${e.supply.name}:${e.days == 0 ? 'out' : 'low'}'
          : e.type;
      first.putIfAbsent(t, () => d);
      counts[t] = (counts[t] ?? 0) + 1;
      if (e is Died) deaths[e.cause.name] = (deaths[e.cause.name] ?? 0) + 1;
      if (vet && e is FellSick) {
        g.me.onAccount = 0;
        g.dispatch(Treat(me, e.camel!));
      }
    }
  }
  final f = g.me.farm;
  // ignore: avoid_print
  print(
    '$name, $span days: head $head0 -> ${g.state.world.aliveOwnedBy(me).length}, '
    'cash $cash0 -> ${g.me.cash.value} (on account ${g.me.onAccount}), '
    'dry days ${f.dryDays}, fed ${f.fedShare}, deaths $deaths',
  );
  final keys = first.keys.toList()..sort((a, b) => first[a]! - first[b]!);
  for (final k in keys) {
    // ignore: avoid_print
    print('   day ${first[k]}: $k x${counts[k]}');
  }
}

/// A jump of [span] days with the stops the design proposes (docs/proposals/rush_and_calendar.md, section 5),
/// checked on the game's state after each day as the jump would: an illness; a death of illness or thirst; a store
/// down to its last 3 days or a day gone short; the money going below zero; the merchant's account at its limit or
/// an order or a treatment refused; an offer; a fine (a treatment found); his round's day; a festival's registration
/// closing in 3 days with a camel of his that could enter and is not entered (once a festival); the breeding season
/// opening with a female the engine lets him breed (once a year); the herd outgrowing its pens. At each stop the
/// "player" does what it asks (treats the sick, fills the store and the tank by orders, as the phone would) and
/// jumps on. [standing]: a standing order, the supplier's top-up sent when a store comes down to 3 days, paid as an
/// order is (cash, then the account to its limit); [vet]: a vet's contract, each illness treated the day it comes,
/// paid as the vet is now (on account when the cash is short) and its monthly fee (the proposed SAR 1,000 and 20 a
/// head, a game choice) taken on the 1st. Nothing is free: what the engine would charge is charged.
void jump(
  String name,
  Game Function() make,
  int span, {
  bool standing = false,
  bool vet = false,
}) {
  final g = make();
  final me = g.me.id;
  final target = g.today + span;
  final stops = <String, int>{};
  final firstStop = <String, int>{};
  final told = <String>{};
  var legs = 1;
  var wasNegative = g.me.cash.isNegative;
  var wasFull = false;
  var wasCrowded = false;
  final sw = Stopwatch()..start();
  final sim = Sim(g.state);

  int fill() {
    // the orders that fill the tank and the store (as the card's buttons and the standing order send them)
    var refused = 0;
    final f = g.me.farm;
    final water = Provisions.fits(f, Supply.water, Balance.waterLoadL);
    final small = Provisions.fits(f, Supply.water, Balance.smallWaterLoadL);
    Result? r;
    if (water > 0) {
      r = g.dispatch(OrderSupply(me, Supply.water, water));
    } else if (small > 0) {
      r = g.dispatch(
        OrderSupply(me, Supply.water, small, tanker: Tanker.small),
      );
    }
    if (r != null && !r.ok) refused++;
    final bags = Provisions.fits(f, Supply.barley, Balance.barleyBagKg);
    if (bags > 1) {
      if (!g.dispatch(OrderSupply(me, Supply.barley, bags * 3 ~/ 10)).ok)
        refused++;
    }
    final bales = Provisions.fits(f, Supply.alfalfa, Balance.alfalfaBaleKg);
    if (bales > 0) {
      if (!g.dispatch(OrderSupply(me, Supply.alfalfa, bales)).ok) refused++;
    }
    return refused;
  }

  bool low() {
    final f = g.me.farm;
    final n = Provisions.needs(
      g.state.world.aliveOwnedBy(me),
      f.feedPlan,
      g.today,
    );
    bool l(double have, double need) =>
        need > 0 && have / need <= Balance.lowStockDays;
    final coming = f.deliveries.isNotEmpty;
    return !coming &&
        (l(f.barleyKg, n.barley) ||
            l(f.alfalfaKg, n.alfalfa) ||
            l(f.waterL, n.water));
  }

  while (g.today < target) {
    final why = <String>{};
    final events = g.advanceDays(1);
    final today = g.today;
    final herd = g.state.world.aliveOwnedBy(me).toList();
    if (vet && today.date.day == 1 && herd.isNotEmpty) {
      sim.pay(g.me, Riyal(-(1000 + 20 * herd.length)), LedgerCategory.vet);
    }
    for (final e in events) {
      if (e.owner != me) continue;
      if (e is FellSick) {
        if (vet) {
          if (!g.dispatch(Treat(me, e.camel!)).ok) why.add('account');
        } else {
          why.add('illness');
        }
      }
      if (e is Died &&
          (e.cause == DeathCause.illness || e.cause == DeathCause.thirst))
        why.add('death');
      if (e is SupplyLow && !standing) why.add('supply');
      if (e is OfferReceived) why.add('offer');
      if (e is TamperingFound || e is SaleRefused) why.add('fine');
    }
    if (standing && low() && fill() > 0) why.add('account');
    if (standing && g.me.farm.dryDays > 0) why.add('supply');
    // money below zero, on the cash itself (the engine's notice comes only on wages day)
    final negative = g.me.cash.isNegative;
    if (negative && !wasNegative) why.add('money');
    wasNegative = negative;
    final full = g.me.onAccount >= Account.limit(herd, g.me, today);
    if (full && !wasFull) why.add('account');
    wasFull = full;
    final crowded = herd.length > g.me.farm.capacity;
    if (crowded && !wasCrowded) why.add('crowded');
    wasCrowded = crowded;
    for (final f in g.state.world.festivals.values) {
      if (f.done) continue;
      for (final r in f.rounds) {
        if (r.day == today && r.entries.any((x) => x.ownerId == me))
          why.add('round');
      }
      if (f.closesOn.daysSince(today) == 3 && told.add('reg ${f.id.value}')) {
        final entered = f.rounds.any(
          (r) => r.entries.any((x) => x.ownerId == me),
        );
        final could =
            !entered &&
            f.rounds.any(
              (r) =>
                  r.size == 1 &&
                  herd.any(
                    (c) =>
                        Eligibility.canEnter(
                          g.state.world,
                          f,
                          r,
                          [c],
                          me,
                          today,
                        ) ==
                        null,
                  ),
            );
        if (could) why.add('registration');
      }
    }
    if (today.month == 11 &&
        today.date.day == 1 &&
        told.add('breed ${today.year}') &&
        herd.any((c) => Eligibility.femaleCanBreed(c, today) == null)) {
      why.add('breeding');
    }
    if (why.isEmpty || g.today >= target) continue;
    legs++;
    final day = g.today.daysSince(target - span);
    for (final w in why) {
      stops[w] = (stops[w] ?? 0) + 1;
      firstStop.putIfAbsent(w, () => day);
    }
    // what the player does at the stop
    for (final c in g.state.world.aliveOwnedBy(me).toList()) {
      if (c.health == HealthStatus.sick) g.dispatch(Treat(me, c.id));
    }
    if (why.contains('supply')) fill();
  }
  // ignore: avoid_print
  print(
    '$name, a jump of $span days: ${legs - 1} stops ($stops, first on day '
    '$firstStop), head ${g.state.world.aliveOwnedBy(me).length}, cash ${g.me.cash.value}, '
    'on account ${g.me.onAccount}, ${sw.elapsedMilliseconds} ms',
  );
}

Game big() {
  final g = start();
  g.me.farm
    ..capacity = 10010
    ..shepherds = 400;
  final sim = Sim(g.state);
  final gen = WorldGen(sim);
  for (var i = 0; i < 9998; i++) {
    gen.makeCamel(sim.rng(['bulk', i]), owner: g.me.id, mean: 50);
  }
  // stores for a month of the herd (a farm of 10,000 head is many farms: the game's one farm holds 56), filled
  final f = g.me.farm;
  final n = Provisions.needs(sim.herdOf(g.me.id), f.feedPlan, g.today);
  f
    ..storeKg = ((n.barley + n.alfalfa) * 30).round()
    ..tankL = (n.water * 30).round()
    ..barleyKg = n.barley * 30
    ..alfalfaKg = n.alfalfa * 30
    ..waterL = n.water * 30;
  return g;
}

/// A farm with the money to run for the stretch: the full farm's year costs about SAR 370,000 (its feed about
/// SAR 840 a day at the standard ration, three shepherds' SAR 54,000, the water), so it is given SAR 400,000; the
/// 10,000 head's season about SAR 14 million, given 20 million (test amounts, so that the stops measured are the
/// farm's, not an empty purse's).
Game Function() rich(Game Function() make, int cash) => () {
  final g = make();
  Sim(g.state).pay(g.me, Riyal(cash), LedgerCategory.opening);
  return g;
};

void main(List<String> args) {
  if (args.contains('stops')) {
    for (final span in [91, 365]) {
      jump('start', start, span);
      jump('full', rich(full, 400000), span);
      jump('full, standing order', rich(full, 400000), span, standing: true);
      jump('full, vet contract', rich(full, 400000), span, vet: true);
      jump('full, both', rich(full, 400000), span, standing: true, vet: true);
    }
    jump(
      '10,000 head, standing order',
      rich(big, 20000000),
      91,
      standing: true,
    );
    jump(
      '10,000 head, both',
      rich(big, 20000000),
      91,
      standing: true,
      vet: true,
    );
    return;
  }
  for (final span in [7, 91, 365]) {
    run('start', start, span);
  }
  for (final span in [7, 91, 365]) {
    run('full', full, span);
  }
  for (final span in [91, 365]) {
    run('full, kept stocked', full, span, topUp: true);
    run(
      'full, kept stocked, every illness treated',
      full,
      span,
      topUp: true,
      vet: true,
    );
  }
}
