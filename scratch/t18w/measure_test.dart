// (scratch, not committed) the day's step, the snapshot and its size at
// 10,000 head, fastest of several runs, as budget_test.dart measures them
import 'dart:convert';

import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:marah_domain/src/world_gen.dart';
import 'package:marah_runtime/src/presenter.dart';
import 'package:marah_runtime/src/snapshot_json.dart';
import 'package:test/test.dart';

void main() {
  test('measure', () {
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
    var day = double.infinity, snap = double.infinity;
    var len = 0;
    for (var i = 0; i < 15; i++) {
      var sw = Stopwatch()..start();
      g.advanceDays(1);
      final d = sw.elapsedMicroseconds / 1000;
      if (d < day) day = d;
      sw = Stopwatch()..start();
      final s = Presenter(g.state, g.me.id).snapshot(1);
      final t = jsonEncode(SnapshotJson.snapshot(s));
      final m = sw.elapsedMicroseconds / 1000;
      if (m < snap) snap = m;
      len = t.length;
    }
    final save = jsonEncode(g.state.toJson()).length;
    // ignore: avoid_print
    print('MEASURE day $day ms snapshot+json $snap ms snapshotChars $len saveChars $save');
  });
}
