// Reviewer's T18 timing: a day's step and the snapshot at 10,000 head, using
// the budget test's own farm (bigFarm, copied verbatim from
// packages/marah_runtime/test/budget_test.dart at b079dce). Day: 30 single
// days, each timed; snapshot: 12 runs, each the first of a new day (day
// advanced untimed before). Prints fastest, median, mean; and the snapshot's
// JSON length. Copy into <checkout>/packages/marah_runtime/test/ and run
// `dart test --concurrency=1 test/r_timing_test.dart` there.
import 'dart:convert';

import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:marah_domain/src/world_gen.dart';
import 'package:marah_runtime/marah_runtime.dart';
import 'package:marah_runtime/src/presenter.dart';
import 'package:test/test.dart';

Game bigFarm() {
  final g = Game.create(
    seed: 3,
    playerName: 'budget',
    farmName: 'budget',
    region: Region.qassim,
    favourite: ColorCategory.majaheem,
    startedAt: DateTime.utc(2026, 11, 8),
  );
  g.me.farm
    ..capacity = 10010
    ..shepherds = 400;
  final sim = Sim(g.state);
  final gen = WorldGen(sim);
  for (var i = 0; i < 9997; i++) {
    gen.makeCamel(sim.rng(['bulk', i]), owner: g.me.id, mean: 55);
  }
  g.me.farm
    ..storeKg = 1 << 30
    ..tankL = 1 << 30
    ..barleyKg = 1e8
    ..alfalfaKg = 1e8
    ..waterL = 1e9;
  g.advanceDays(30);
  return g;
}

String stats(List<double> xs) {
  final s = [...xs]..sort();
  final mean = s.reduce((a, b) => a + b) / s.length;
  return 'fastest ${s.first.toStringAsFixed(1)} median '
      '${s[s.length ~/ 2].toStringAsFixed(1)} mean ${mean.toStringAsFixed(1)}';
}

void main() {
  test('reviewer timing', () {
    final g = bigFarm();
    final day = <double>[];
    for (var i = 0; i < 30; i++) {
      final sw = Stopwatch()..start();
      g.advanceDays(1);
      day.add(sw.elapsedMicroseconds / 1000);
    }
    final snap = <double>[];
    var len = 0;
    for (var i = 0; i < 12; i++) {
      g.advanceDays(1);
      final sw = Stopwatch()..start();
      final s = Presenter(g.state, g.me.id).snapshot(1);
      snap.add(sw.elapsedMicroseconds / 1000);
      len = jsonEncode(SnapshotJson.snapshot(s)).length;
    }
    // ignore: avoid_print
    print('RTIME day ms ${stats(day)} | snapshot ms ${stats(snap)} | '
        'snapshot json $len chars');
  }, timeout: const Timeout(Duration(minutes: 10)));
}
