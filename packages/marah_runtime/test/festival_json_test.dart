// The festival page and the snapshot as the phone gets them: places,
// prizes and the stage an entry left at, never a score or a mark (hidden
// values; the design: «والدرجات ما تنعلن»).
import 'dart:convert';

import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:marah_domain/src/world_gen.dart';
import 'package:marah_domain/testing.dart';
import 'package:marah_runtime/marah_runtime.dart';
import 'package:marah_runtime/src/presenter.dart';
import 'package:test/test.dart';

void main() {
  test('a judged round with the player\'s camel: no score, no marks', () {
    final g = Game.create(
      seed: 42,
      playerName: 'p',
      farmName: 'f',
      region: Region.qassim,
      favourite: ColorCategory.wodh,
      startedAt: DateTime.utc(2026, 11, 8),
    );
    grant(g, 1000000);
    g.me.farm
      ..storeKg = 1 << 30
      ..tankL = 1 << 30
      ..barleyKg = 1e8
      ..alfalfaKg = 1e8
      ..waterL = 1e9;
    final f = g.state.world.festivals.values.firstWhere(
      (f) => f.tier == FestivalTier.grand,
    );
    final r = f.rounds.firstWhere(
      (r) => r.kind == RoundKind.mafareed && r.sex == Sex.female,
    );
    final sim = Sim(g.state);
    final c = WorldGen(sim).makeCamel(
      sim.rng(['json']),
      owner: g.me.id,
      mean: 90,
      category: r.category,
      sex: Sex.female,
      ageDays: AgeClass.mafrood.minDays + 150 - r.day.daysSince(g.today),
    )..acquiredOn = g.today - 200;
    c.genes[Trait.coat] = 80;
    g.advanceTo(f.opensOn);
    expect(g.dispatch(EnterRound(g.me.id, f.id, r.id, [c.id])).ok, isTrue);
    g.advanceTo(r.day);
    expect(r.judged, isTrue);
    final p = Presenter(g.state, g.me.id);
    final page = jsonEncode(
      SnapshotJson.festivalDetail(p.festivalDetail(f.id)!),
    );
    final snap = jsonEncode(SnapshotJson.snapshot(p.snapshot(1)));
    expect(page, contains('"rank"'));
    for (final text in [page, snap]) {
      expect(text, isNot(contains('"score"')));
      expect(text, isNot(contains('"marks"')));
    }
  });
}
