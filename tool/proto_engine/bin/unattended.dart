// What happens when days pass and nobody tends the farm (task T15, the calendar's design:
// docs/proposals/rush_and_calendar.md), by the engine's own rules: a game left alone for a week, a season (91 days)
// and a year, and what each stretch brought, by the engine's events. A measurement, not the game.
//
//   dart run tool/proto_engine/bin/unattended.dart
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

void main() {
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
