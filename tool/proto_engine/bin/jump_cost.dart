// What a jump forward costs (task T15, the calendar's design: docs/proposals/rush_and_calendar.md): the engine's own
// daily pipeline run for a week, a season (91 days) and a year at three herds (the start's two head; the farm full
// at 56, the most its facilities hold, GDD 4.1; and 10,000 head, the most a player may hold, ADR 0004), then the
// save written and the screen's snapshot made, as EngineCore does at the end of a catch-up. A measurement, not the
// game. Stores are filled for the run (as the budget test does): the cost of a herd that lives, not of one dying.
//
//   dart run tool/proto_engine/bin/jump_cost.dart                (the VM)
//   dart compile js -O2 tool/proto_engine/bin/jump_cost.dart -o $SC/jc.js && node $SC/jc.js   (JavaScript)
//
// Prints one line a herd and span: the days' time (ms), the slowest single day, the save's encoding and the
// snapshot, and the events the stretch made.
import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:marah_domain/src/world_gen.dart';
import 'package:marah_runtime/src/presenter.dart';
import 'package:marah_runtime/src/snapshot_json.dart';

Game farm(int head) {
  final g = Game.create(
    seed: 4242,
    playerName: 'jump',
    farmName: 'jump',
    region: Region.qassim,
    favourite: ColorCategory.wodh,
    startedAt: DateTime.utc(2026, 11, 14),
  );
  final f = g.me.farm;
  if (head > 2) {
    f
      ..capacity = head + 10
      ..shepherds = (head / Balance.camelsPerShepherd).ceil();
    final sim = Sim(g.state);
    final gen = WorldGen(sim);
    for (var i = 0; i < head - 2; i++) {
      gen.makeCamel(sim.rng(['bulk', i]), owner: g.me.id, mean: 50);
    }
  }
  f
    ..storeKg = 1 << 30
    ..tankL = 1 << 30
    ..barleyKg = 1e8
    ..alfalfaKg = 1e8
    ..waterL = 1e9;
  return g;
}

void main() {
  // warm up the compiler on a small farm (the first run of anything is slower on the VM and in V8 alike)
  farm(56).advanceDays(60);
  for (final head in [2, 56, 10000]) {
    for (final span in [7, 91, 365]) {
      final g = farm(head);
      final sw = Stopwatch()..start();
      var slowest = 0;
      var events = 0;
      for (var d = 0; d < span; d++) {
        final t = sw.elapsedMicroseconds;
        events += g.advanceDays(1).length;
        final one = sw.elapsedMicroseconds - t;
        if (one > slowest) slowest = one;
      }
      final simMs = sw.elapsedMicroseconds / 1000;
      sw.reset();
      final saved = const SaveCodec().encode(g.state);
      final saveMs = sw.elapsedMicroseconds / 1000;
      sw.reset();
      final snap = SnapshotJson.snapshot(
        Presenter(g.state, g.me.id).snapshot(1),
      );
      final snapMs = sw.elapsedMicroseconds / 1000;
      final alive = g.state.world.aliveOwnedBy(g.me.id).length;
      // ignore: avoid_print
      print(
        'head $head span $span: days ${simMs.toStringAsFixed(1)} ms '
        '(${(simMs / span).toStringAsFixed(2)} a day, slowest ${(slowest / 1000).toStringAsFixed(1)}), '
        'save ${saveMs.toStringAsFixed(1)} ms (${(saved.length / 1e6).toStringAsFixed(2)} MB), '
        'snapshot ${snapMs.toStringAsFixed(1)} ms (${snap.length} keys), events $events, alive $alive',
      );
    }
  }
}
