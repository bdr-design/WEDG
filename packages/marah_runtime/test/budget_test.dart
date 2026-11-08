// Performance budgets for the worker. They fail when a change makes the
// engine an order of magnitude heavier, long before players would feel it.
// Limits are generous (shared CI machines are noisy); measured values on a
// desktop CPU are noted next to each limit.
import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:marah_domain/src/world_gen.dart';
import 'package:marah_runtime/src/presenter.dart';
import 'package:test/test.dart';

/// A large farm: 300 head, well beyond what most players will keep.
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
    ..capacity = 320
    ..shepherds = 12;
  final sim = Sim(g.state);
  final gen = WorldGen(sim);
  for (var i = 0; i < 297; i++) {
    gen.makeCamel(sim.rng(['bulk', i]), owner: g.me.id, mean: 55);
  }
  g.advanceDays(30); // warm up
  return g;
}

double avgMs(void Function() f, int reps) {
  final sw = Stopwatch()..start();
  for (var i = 0; i < reps; i++) {
    f();
  }
  return sw.elapsedMicroseconds / reps / 1000;
}

void main() {
  late Game g;
  setUpAll(() => g = bigFarm());

  test('one game day stays under 5 ms (measured ~0.4 ms)', () {
    expect(avgMs(() => g.advanceDays(1), 60), lessThan(5));
  });

  test('a command stays under 2 ms (measured < 0.1 ms)', () {
    expect(
      avgMs(() => g.dispatch(SetFeedPlan(g.me.id, FeedPlan.standard)), 50),
      lessThan(2),
    );
  });

  test('building the screen snapshot stays under 25 ms (measured ~2.3 ms)', () {
    expect(
      avgMs(() => Presenter(g.state, g.me.id).snapshot(1), 20),
      lessThan(25),
    );
  });

  test('the save stays under 600 KB and encodes under 40 ms '
      '(measured 237 KB, ~4 ms)', () {
    const codec = SaveCodec();
    final text = codec.encode(g.state);
    expect(text.length, lessThan(600 * 1024));
    expect(avgMs(() => codec.encode(g.state), 10), lessThan(40));
  });
}
