// Performance budgets for the worker. They fail when a change makes the
// engine an order of magnitude heavier, long before players would feel it.
// Limits are generous (shared CI machines are noisy); measured values on a
// desktop CPU are noted next to each limit.
import 'dart:convert';

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

/// The fastest of [reps] runs: the work's own cost, steady on a shared
/// machine where another process's spike can stretch any one run (the
/// budgets below once failed only under load). With [newDay], each run is
/// the first of a new day (the day advanced untimed before it), so the
/// herd's looks are worked out afresh, as the first snapshot and the first
/// festival page of a day do (a later one reuses them).
double fastestMs(void Function() f, int reps, {void Function()? newDay}) {
  var best = double.infinity;
  for (var i = 0; i < reps; i++) {
    newDay?.call();
    final sw = Stopwatch()..start();
    f();
    final ms = sw.elapsedMicroseconds / 1000;
    if (ms < best) best = ms;
  }
  return best;
}

void main() {
  late Game g;
  setUpAll(() => g = bigFarm());

  test('one game day stays under 150 ms at 10,000 head', () {
    expect(g.state.world.aliveOwnedBy(g.me.id).length, greaterThan(9800));
    expect(fastestMs(() => g.advanceDays(1), 10), lessThan(150));
    expect(g.me.farm.dryDays, 0);
    expect(g.me.farm.fedShare, 1);
  });

  test('a command stays under 2 ms (measured < 0.1 ms)', () {
    expect(
      fastestMs(() => g.dispatch(SetFeedPlan(g.me.id, FeedPlan.standard)), 50),
      lessThan(2),
    );
  });

  test('the screen snapshot stays under 250 ms at 10,000 head', () {
    expect(
      fastestMs(
        () => Presenter(g.state, g.me.id).snapshot(1),
        5,
        newDay: () => g.advanceDays(1),
      ),
      lessThan(250),
    );
  });

  test('a page of 50 from 10,000 stays under 150 ms', () {
    expect(
      fastestMs(
        () => Presenter(g.state, g.me.id).herdPage(const HerdQuery()),
        5,
      ),
      lessThan(150),
    );
  });

  test('a festival\'s page stays under 250 ms at 10,000 head', () {
    final f = g.state.world.festivals.values.firstWhere(
      (f) => f.tier == FestivalTier.grand,
    );
    expect(
      fastestMs(
        () => Presenter(g.state, g.me.id).festivalDetail(f.id),
        3,
        newDay: () => g.advanceDays(1),
      ),
      lessThan(250),
    );
  });

  test(
    'the snapshot stays bounded with a thousand sick (the review\'s B3)',
    () {
      final sick = g.state.world.aliveOwnedBy(g.me.id).take(1000).toList();
      final was = [for (final c in sick) (c.health, c.illness, c.sickSince)];
      for (final c in sick) {
        c
          ..health = HealthStatus.sick
          ..illness = Illness.mange
          ..sickSince = g.today;
      }
      try {
        final snap = Presenter(g.state, g.me.id).snapshot(1);
        final text = jsonEncode(SnapshotJson.snapshot(snap));
        final rush = snap.rush;
        expect((rush['sick']! as List).length, 20);
        expect(rush['sickCount'], greaterThanOrEqualTo(1000));
        expect(rush['treatAll'], greaterThan(0));
        // (measured 59.7k at day one; 240k with every sick camel listed)
        expect(text.length, lessThan(80000));
        // ignore: avoid_print
        print('10k head, 1,000 sick: snapshot ${text.length} characters');
      } finally {
        for (var i = 0; i < sick.length; i++) {
          sick[i]
            ..health = was[i].$1
            ..illness = was[i].$2
            ..sickSince = was[i].$3;
        }
      }
    },
  );

  test('measured values', () {
    final day = avgMs(() => g.advanceDays(1), 10);
    // a new day before each: the first look at the herd that day
    final snap =
        avgMs(() {
          g.advanceDays(1);
          Presenter(g.state, g.me.id).snapshot(1);
        }, 5) -
        day;
    final page = avgMs(
      () => Presenter(g.state, g.me.id).herdPage(const HerdQuery()),
      5,
    );
    final grand = g.state.world.festivals.values.firstWhere(
      (f) => f.tier == FestivalTier.grand,
    );
    final fest =
        avgMs(() {
          g.advanceDays(1);
          Presenter(g.state, g.me.id).festivalDetail(grand.id);
        }, 3) -
        day;
    // ignore: avoid_print
    print(
      '10k head: day ${day.toStringAsFixed(1)} ms, snapshot '
      '${snap.toStringAsFixed(1)} ms, page ${page.toStringAsFixed(1)} ms, '
      'festival ${fest.toStringAsFixed(1)} ms',
    );
  });
}
