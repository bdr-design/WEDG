// What a year's jump costs with the built away call (task T15, part B): AwayRun day by day to a year ahead, the
// player going on after each stop, at 56 head (the full farm) and 10,000 head (ADR 0004's most), with the standing
// orders and the vet's contract on (without them a large herd stops every day). A measurement, not the game.
//
//   dart run tool/proto_engine/bin/away_cost.dart
//   dart compile js -O2 tool/proto_engine/bin/away_cost.dart -o ac.js && node ac.js
import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:marah_domain/src/world_gen.dart';

Game farm(int head) {
  final g = Game.create(
    seed: 4242,
    playerName: 'away',
    farmName: 'away',
    region: Region.qassim,
    favourite: ColorCategory.wodh,
    startedAt: DateTime.utc(2026, 11, 14),
  );
  final sim = Sim(g.state);
  final gen = WorldGen(sim);
  for (var i = 0; i < head - 2; i++) {
    gen.makeCamel(sim.rng(['bulk', i]), owner: g.me.id, mean: 50);
  }
  final f = g.me.farm
    ..capacity = head + 10
    ..shepherds = (head / Balance.camelsPerShepherd).ceil();
  final n = Provisions.needs(sim.herdOf(g.me.id), f.feedPlan, g.today);
  f
    ..storeKg = ((n.barley + n.alfalfa) * 30).round()
    ..tankL = (n.water * 30).round()
    ..barleyKg = n.barley * 30
    ..alfalfaKg = n.alfalfa * 30
    ..waterL = n.water * 30;
  sim.pay(g.me, Riyal(head * 20000), LedgerCategory.opening);
  final me = g.me.id;
  g
    ..dispatch(SetStandingOrder(me, StandingOrder.water, on: true))
    ..dispatch(SetStandingOrder(me, StandingOrder.feed, on: true))
    ..dispatch(SignVetContract(me));
  return g;
}

void main() {
  farm(56).advanceDays(30); // warm up
  for (final head in [56, 10000]) {
    final g = farm(head);
    final target = g.today + 365;
    final stops = <String>[];
    var slowest = 0;
    final sw = Stopwatch()..start();
    while (g.today < target) {
      final run = AwayRun(g, AwayPlan(target));
      while (!run.done) {
        final t = sw.elapsedMicroseconds;
        run.step();
        final d = sw.elapsedMicroseconds - t;
        if (d > slowest) slowest = d;
      }
      stops.add(run.stop!.kind.name);
    }
    final ms = sw.elapsedMicroseconds / 1000;
    sw.reset();
    final save = const SaveCodec().encode(g.state);
    // ignore: avoid_print
    print(
      'head $head, a year away: ${ms.toStringAsFixed(0)} ms '
      '(slowest day ${(slowest / 1000).toStringAsFixed(1)} ms), '
      '${stops.length} legs ${stops.join(' ')}, save ${sw.elapsedMilliseconds} ms '
      '${(save.length / 1e6).toStringAsFixed(2)} MB, '
      'alive ${g.state.world.aliveOwnedBy(g.me.id).length}',
    );
  }
}
