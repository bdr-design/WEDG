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
    expect(avgMs(() => g.advanceDays(1), 10), lessThan(150));
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
