// Reviewer: the snapshot's size on a new game, and the falcons key's share
// (static part = routes, permits' fixed fields, gear catalog, grounds).
import 'dart:convert';
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_runtime/marah_runtime.dart';
import 'package:marah_runtime/src/presenter.dart';
import 'package:test/test.dart';

void main() {
  test('sizes', () {
    final g = Game.create(seed: 4242, playerName: 'a', farmName: 'b',
        region: Region.qassim, favourite: ColorCategory.majaheem,
        startedAt: DateTime.utc(2026, 11, 1));
    for (final d in [0, 5]) {
      if (d > 0) g.advanceDays(d);
      final s = Presenter(g.state, g.me.id).snapshot(1);
      final all = jsonEncode(SnapshotJson.snapshot(s)).length;
      final f = s.falcons;
      final fl = jsonEncode(f).length;
      int k(String key) => jsonEncode(f[key]).length;
      // ignore: avoid_print
      print('RSIZE day ${g.today.value} snapshot $all falcons $fl '
          'routes ${k('routes')} permits ${k('permits')} gear ${k('gear')} '
          'grounds ${k('grounds')} room ${k('room')} lots ${k('lots')}');
      final sw = Stopwatch()..start();
      for (var i = 0; i < 200; i++) { falconFacts(g.state, g.me.id); }
      // ignore: avoid_print
      print('RSIZE falconFacts ${(sw.elapsedMicroseconds / 200).toStringAsFixed(0)} us');
    }
  });
}
