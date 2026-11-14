// Reviewer: CPU time of the 10k-head farm's days (compiled to an exe and run
// under bash's `time`, whose user figure is less hurt by other processes).
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:marah_domain/src/world_gen.dart';

void main() {
  final g = Game.create(seed: 3, playerName: 'b', farmName: 'b',
      region: Region.qassim, favourite: ColorCategory.majaheem,
      startedAt: DateTime.utc(2026, 11, 8));
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
  final sw = Stopwatch()..start();
  g.advanceDays(150);
  // ignore: avoid_print
  print('RCPU 150 days ${sw.elapsedMilliseconds} ms');
}
