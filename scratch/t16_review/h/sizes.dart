// T10 reviewer's probe: snapshot and festival page JSON size and build time at day one, one year, ten years
// (a Bot playing: it enters festivals, dyes some), and at 10,000 head. Copy into <checkout>/packages/marah_runtime/tool_rv/
// and `dart compile exe` it, run `bot|big`. Uses only APIs present at the base (c25de25).
import 'dart:convert';
import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/testing.dart';
import 'package:marah_runtime/marah_runtime.dart';
import 'package:marah_runtime/src/presenter.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:marah_domain/src/world_gen.dart';

String _d(GameDay d) => d.date.toIso8601String().substring(0, 10);

void measure(Game g, String label, {int reps = 40, bool newDay = false}) {
  final me = g.me;
  PlayerSnapshot? prev;
  final times = <int>[];
  final first = <int>[];
  var snapBytes = 0;
  final keys = <String, int>{};
  for (var i = 0; i < reps; i++) {
    final sw = Stopwatch()..start();
    final s = Presenter(g.state, me.id).snapshot(i + 1, previous: prev);
    final m = SnapshotJson.snapshot(s);
    final j = jsonEncode(m);
    sw.stop();
    (i == 0 ? first : times).add(sw.elapsedMicroseconds);
    snapBytes = utf8.encode(j).length;
    if (i == 0) for (final e in m.entries) keys[e.key] = utf8.encode(jsonEncode(e.value)).length;
    prev = s;
  }
  times.sort();
  // every festival's page: the largest and its time (the median of 5)
  var pageMax = 0, pageSum = 0, pages = 0;
  String? pageMaxName;
  final pt = <int>[];
  for (final f in g.state.world.festivals.values) {
    final sw = Stopwatch()..start();
    final d = Presenter(g.state, me.id).festivalDetail(f.id);
    if (d == null) continue;
    final b = utf8.encode(jsonEncode(SnapshotJson.festivalDetail(d))).length;
    sw.stop();
    pt.add(sw.elapsedMicroseconds);
    pages++;
    pageSum += b;
    if (b > pageMax) { pageMax = b; pageMaxName = '${f.name} ${f.tier.name}'; }
  }
  pt.sort();
  final save = utf8.encode(const SaveCodec().encode(g.state)).length;
  final big = (keys.entries.toList()..sort((a, b) => b.value - a.value)).take(6).map((e) => '${e.key}=${e.value}').join(' ');
  print('$label | day ${g.today.value} ${_d(g.today)} | herd ${g.state.world.aliveOwnedBy(me.id).length} | cash ${me.cash.value} '
      '| snapshot $snapBytes B, first ${first.first} us, median ${times.isEmpty ? '-' : times[times.length ~/ 2]} us '
      '| fest pages $pages: max $pageMax B ($pageMaxName), sum $pageSum B, time median ${pt.isEmpty ? '-' : pt[pt.length ~/ 2]} us max ${pt.isEmpty ? '-' : pt.last} us '
      '| save $save B | top keys $big');
}

void main(List<String> a) {
  final mode = a.isEmpty ? 'bot' : a[0];
  if (mode == 'big') {
    final g = Game.create(seed: 3, playerName: 'budget', farmName: 'budget', region: Region.qassim,
        favourite: ColorCategory.majaheem, startedAt: DateTime.utc(2026, 11, 8));
    g.me.farm..capacity = 10010..shepherds = 400;
    final sim = Sim(g.state);
    final gen = WorldGen(sim);
    for (var i = 0; i < 9997; i++) { gen.makeCamel(sim.rng(['bulk', i]), owner: g.me.id, mean: 55); }
    g.me.farm..storeKg = 1 << 30..tankL = 1 << 30..barleyKg = 1e8..alfalfaKg = 1e8..waterL = 1e9;
    g.advanceDays(30);
    measure(g, 'big 10k', reps: 6);
    // the grand festival's page on a new day (first look), fastest of 3
    final grand = g.state.world.festivals.values.firstWhere((f) => f.tier == FestivalTier.grand);
    var best = 1 << 40, bytes = 0;
    for (var i = 0; i < 3; i++) {
      g.advanceDays(1);
      final sw = Stopwatch()..start();
      final d = Presenter(g.state, g.me.id).festivalDetail(grand.id)!;
      bytes = utf8.encode(jsonEncode(SnapshotJson.festivalDetail(d))).length;
      sw.stop();
      if (sw.elapsedMicroseconds < best) best = sw.elapsedMicroseconds;
    }
    print('big 10k grand page (new day, fastest of 3): $bytes B, $best us');
    return;
  }
  // the page's new game: seed 4242, qassim, wodh, 1 Oct 2026 (the design's games)
  final g = Game.create(seed: 4242, playerName: 'اللاعب', farmName: 'العزبة',
      region: Region.qassim, favourite: ColorCategory.wodh, startedAt: DateTime.utc(2026, 10, 1));
  if (mode == 'rich') grant(g, 580000);
  final bot = Bot(g);
  measure(g, '$mode day1');
  final start = g.today;
  for (final y in [1, 10]) {
    final target = GameDay.ofDate(DateTime.utc(start.date.year + y, start.date.month, start.date.day));
    while (g.today.value < target.value) {
      bot.act();
      g.advanceDays(7);
    }
    measure(g, '$mode ${y}y');
  }
}
