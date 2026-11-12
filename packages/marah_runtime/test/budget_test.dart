// Performance budgets for the worker. They fail when a change makes the
// engine an order of magnitude heavier, long before players would feel it.
// Limits are generous (shared CI machines are noisy); measured values on a
// desktop CPU are noted next to each limit.
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:marah_domain/src/world_gen.dart';
import 'package:marah_runtime/marah_runtime.dart';
import 'package:marah_runtime/src/presenter.dart';
import 'package:test/test.dart';

/// The largest farm a player may hold: 10,000 head (ADR 0004).
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
  // a store and a tank for 10,000 head, filled for the run (empty, the herd
  // starved and died of thirst and the budgets measured a shrinking farm)
  g.me.farm
    ..storeKg = 1 << 30
    ..tankL = 1 << 30
    ..barleyKg = 1e8
    ..alfalfaKg = 1e8
    ..waterL = 1e9;
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

  test('one game day stays under 150 ms at 10,000 head', () {
    expect(g.state.world.aliveOwnedBy(g.me.id).length, greaterThan(9800));
    expect(avgMs(() => g.advanceDays(1), 10), lessThan(150));
    expect(g.me.farm.dryDays, 0);
    expect(g.me.farm.fedShare, 1);
  });

  test('a command stays under 2 ms (measured < 0.1 ms)', () {
    expect(
      avgMs(() => g.dispatch(SetFeedPlan(g.me.id, FeedPlan.standard)), 50),
      lessThan(2),
    );
  });

  test('the screen snapshot stays under 250 ms at 10,000 head', () {
    expect(
      avgMs(() => Presenter(g.state, g.me.id).snapshot(1), 5),
      lessThan(250),
    );
  });

  test('a page of 50 from 10,000 stays under 150 ms', () {
    expect(
      avgMs(() => Presenter(g.state, g.me.id).herdPage(const HerdQuery()), 5),
      lessThan(150),
    );
  });

  test('a winter day costs about what an autumn day does', () {
    // the pasture's months (December to April): its draw was made for every
    // camel every day, and a January day took up to twice an autumn one (the
    // review of 57ab698; 1.3 to 1.4x here, a noisy guess for a guard, so
    // this catches a gross return of it only); measured now 0.9 to 1.0x
    final w = bigFarm();
    // the best of three runs of ten days each (shared machines are noisy)
    double best() =>
        [for (var i = 0; i < 3; i++) avgMs(() => w.advanceDays(1), 10)]
            .reduce((a, b) => a < b ? a : b);
    final autumn = best();
    while (w.today.month != 1) {
      w.advanceDays(1);
    }
    final winter = best();
    // ignore: avoid_print
    print(
      '10k head: an autumn day ${autumn.toStringAsFixed(1)} ms, a January '
      'day ${winter.toStringAsFixed(1)} ms',
    );
    expect(winter, lessThan(autumn * 1.5 + 0.5));
  });

  test('measured values', () {
    final day = avgMs(() => g.advanceDays(1), 10);
    final snap = avgMs(() => Presenter(g.state, g.me.id).snapshot(1), 5);
    final page = avgMs(
      () => Presenter(g.state, g.me.id).herdPage(const HerdQuery()),
      5,
    );
    // ignore: avoid_print
    print(
      '10k head: day ${day.toStringAsFixed(1)} ms, snapshot '
      '${snap.toStringAsFixed(1)} ms, page ${page.toStringAsFixed(1)} ms',
    );
  });
}
