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
    // judged at dawn, nothing told yet: no place, no field in the page
    final dawn = jsonEncode(
      SnapshotJson.festivalDetail(
        Presenter(g.state, g.me.id).festivalDetail(f.id)!,
      ),
    );
    expect(dawn, isNot(contains('"rank"')));
    g.tellTo(Game.minutesInDay);
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

  test('what المزاين and «المحادثات» are told (seed 4242, day one)', () {
    final g = Game.create(
      seed: 4242,
      playerName: 'p',
      farmName: 'f',
      region: Region.qassim,
      favourite: ColorCategory.wodh,
      startedAt: DateTime.utc(2026, 10),
    );
    final v = GameView(g.state, g.me.id);
    final f = v.festivals.firstWhere(
      (f) => !f.done && f.opensOn <= g.today && g.today <= f.closesOn,
    );
    // a market camel bought: on the truck, owned too recently
    final l = v.market.reduce(
      (a, b) => a.askPrice.value <= b.askPrice.value ? a : b,
    );
    final bought = g.dispatch(BuyListing(g.me.id, l.id));
    expect(bought.ok, isTrue);
    final p = Presenter(g.state, g.me.id);
    final page = SnapshotJson.festivalDetail(p.festivalDetail(f.id)!);
    final reg = page['register']! as List<Object?>;
    expect(page['registerTotal'], 3);
    expect(reg, hasLength(3));
    final truck = reg.cast<Map<String, Object?>>().firstWhere(
      (x) => (x['camel']! as Map)['onTheWay'] == true,
    );
    expect(truck['error'], isNotNull);
    // the she-camel may enter her own round
    final dam = reg.cast<Map<String, Object?>>().firstWhere(
      (x) => (x['camel']! as Map)['ageName'] == 'سديسة',
      orElse: () => reg.cast<Map<String, Object?>>().firstWhere(
        (x) => x['error'] == null,
      ),
    );
    final card = page['festival']! as Map<String, Object?>;
    expect(card['topEnterable'], greaterThan(0));
    expect(card['topEnterableKind'], isNotNull);
    // registered: the treatment man's message, unread, in the snapshot
    final camel = (dam['camel']! as Map)['id']! as String;
    expect(
      g
          .dispatch(
            EnterRound(g.me.id, f.id, RoundId(dam['round']! as String), [
              CamelId(camel),
            ]),
          )
          .ok,
      isTrue,
    );
    final snap = SnapshotJson.snapshot(Presenter(g.state, g.me.id).snapshot(1));
    final dealer = snap['dealer']! as Map<String, Object?>;
    expect(dealer['name'], Balance.dealerName);
    expect(dealer['unread'], 1);
    final m = (dealer['messages']! as List).single as Map<String, Object?>;
    expect((m['camel'], m['festival'], m['read']), (camel, f.id.value, false));
    expect(m['roundDay'], isNotNull);
    expect(snap['findings'], isEmpty);
    // الصيت by its band, never a number
    for (final b in (snap['reputation']! as Map).values) {
      expect(b, isA<String>());
    }
    // the entry on the festival's card, nothing told
    final e =
        ((snap['festivals']! as List).cast<Map<String, Object?>>().firstWhere(
                  (x) => x['id'] == f.id.value,
                )['entries']!
                as List)
            .single;
    expect((e as Map)['told'], 0);
    // each tanker says whether it goes and what goes on account
    final farm = snap['farm']! as Map<String, Object?>;
    for (final t in farm['tankers']! as List) {
      expect((t as Map)['goes'], isA<bool>());
    }
    expect((farm['account']! as Map)['spend'], isA<int>());
    expect(
      ((snap['festivalRules']! as Map)['stageMinutes']! as List),
      Balance.stageMinutes,
    );
  });
}
