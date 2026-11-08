// Measures the costs that would hit the UI thread if run there:
// catch-up of N game days, save encode/decode, and building views.
// Run: dart run tool/bench.dart  (from the repo root, via the domain package)
import 'dart:convert';

import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/testing.dart';

void main() {
  final g = Game.create(
    seed: 99,
    playerName: 'bench',
    farmName: 'bench',
    region: Region.qassim,
    favourite: ColorCategory.majaheem,
  );
  final bot = Bot(g);
  for (var i = 0; i < 52 * 4; i++) {
    bot.week();
  }
  final herd = g.state.world.aliveOwnedBy(g.me.id).length;
  print('after 4 years: herd $herd, registry ${g.state.world.camels.length}');

  T time<T>(String label, T Function() f, {int reps = 5}) {
    late T r;
    final sw = Stopwatch()..start();
    for (var i = 0; i < reps; i++) {
      r = f();
    }
    sw.stop();
    print('${label.padRight(34)} ${(sw.elapsedMicroseconds / reps / 1000).toStringAsFixed(2)} ms');
    return r;
  }

  const codec = SaveCodec();
  final text = time('encode save', () => codec.encode(g.state));
  print('save size ${(text.length / 1024).toStringAsFixed(0)} KB');
  time('decode save', () => codec.decode(text));
  time('jsonDecode only', () => jsonDecode(text));
  time('catch-up 7 days (1 real day)', () {
    final c = Game((codec.decode(text) as Loaded).state);
    return c.advanceDays(7);
  });
  time('catch-up 210 days (30 real days)', () {
    final c = Game((codec.decode(text) as Loaded).state);
    return c.advanceDays(210);
  }, reps: 3);
  time('view: herd with estimates', () {
    final v = GameView(g.state, g.me.id);
    return [for (final c in v.herd) (c.quality, c.estimate, c.looks)];
  });
  time('view: market with estimates', () {
    final v = GameView(g.state, g.me.id);
    return [for (final l in v.market) (l.camel.quality, l.camel.estimate)];
  });
  time('view: herd value', () => GameView(g.state, g.me.id).herdValue);
}
