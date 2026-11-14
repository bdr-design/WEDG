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

/// A jump of [span] days with the stops the design proposes (docs/proposals/rush_and_calendar.md): it hands the game
/// back on an illness, a death, a store down to its last days, money below zero, an offer or a treatment found; the
/// "player" then does what each asks (treats the camel, fills the store and the tank) and jumps on to the same day.
/// [standing]: the store and the tank kept full (a standing order); [vet]: each illness treated the day it comes (a
/// vet's contract), so neither stops the jump.
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
  var legs = 1;
  final sw = Stopwatch()..start();
  while (g.today < target) {
    if (standing) {
      final f = g.me.farm;
      f
        ..barleyKg = f.storeKg * 0.3
        ..alfalfaKg = f.storeKg * 0.7
        ..waterL = f.tankL.toDouble();
    }
    final why = <String>{};
    for (final e in g.advanceDays(1)) {
      if (e.owner != me) continue;
      if (e is FellSick) {
        if (vet) {
          g.me.onAccount = 0;
          g.dispatch(Treat(me, e.camel!));
        } else {
          why.add('illness');
        }
      }
      if (e is Died) why.add('death');
      if (e is SupplyLow) why.add('supply');
      if (e is CashNegative) why.add('money');
      if (e is OfferReceived) why.add('offer');
      if (e is TamperingFound) why.add('found');
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
    if (why.contains('supply')) {
      final f = g.me.farm;
      final water = Provisions.fits(f, Supply.water, Balance.waterLoadL);
      if (water > 0) {
        g.dispatch(OrderSupply(me, Supply.water, water));
      } else {
        final small = Provisions.fits(f, Supply.water, Balance.smallWaterLoadL);
        if (small > 0) {
          g.dispatch(
            OrderSupply(me, Supply.water, small, tanker: Tanker.small),
          );
        }
      }
      final bags = Provisions.fits(f, Supply.barley, Balance.barleyBagKg);
      if (bags > 1) g.dispatch(OrderSupply(me, Supply.barley, bags * 3 ~/ 10));
      final bales = Provisions.fits(f, Supply.alfalfa, Balance.alfalfaBaleKg);
      if (bales > 0) g.dispatch(OrderSupply(me, Supply.alfalfa, bales));
    }
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
    ..shepherds = 400
    ..storeKg = 1 << 30
    ..tankL = 1 << 30;
  final sim = Sim(g.state);
  final gen = WorldGen(sim);
  for (var i = 0; i < 9998; i++) {
    gen.makeCamel(sim.rng(['bulk', i]), owner: g.me.id, mean: 50);
  }
  return g;
}

void main(List<String> args) {
  if (args.contains('stops')) {
    for (final span in [91, 365]) {
      jump('start', start, span);
      jump('full', full, span);
      jump('full, standing order', full, span, standing: true);
      jump('full, vet contract', full, span, vet: true);
      jump('full, both', full, span, standing: true, vet: true);
    }
    jump('10,000 head, standing order', big, 91, standing: true);
    jump('10,000 head, both', big, 91, standing: true, vet: true);
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
