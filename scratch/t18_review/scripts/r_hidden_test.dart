// Reviewer: hidden values in the whole snapshot JSON (copy into marah_runtime/test/).
import 'dart:convert';
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:marah_runtime/marah_runtime.dart';
import 'package:marah_runtime/src/presenter.dart';
import 'package:test/test.dart';

void main() {
  test('hidden', () {
    final g = Game.create(seed: 4242, playerName: 'p', farmName: 'f',
        region: Region.qassim, favourite: ColorCategory.wodh,
        startDay: GameDay.ofDate(DateTime.utc(2026, 10, 1)),
        startedAt: DateTime.utc(2026, 11, 14));
    Sim(g.state).pay(g.me, const Riyal(5000000), LedgerCategory.opening);
    g.dispatch(BuildFacility(g.me.id, Facility.falconRoom));
    g.advanceDays(Balance.buildDays);
    final ex = FalconMarket.lots(g.state.world.seed, FalconRoute.exhibition, g.today);
    g.dispatch(BuyFalcon(g.me.id, ex.first.key));
    final text = jsonEncode(SnapshotJson.snapshot(Presenter(g.state, g.me.id).snapshot(1)));
    final keys = RegExp(r'"([A-Za-z]+)":').allMatches(jsonEncode(SnapshotJson.snapshot(Presenter(g.state, g.me.id).snapshot(1))['falcons'])).map((m) => m[1]).toSet();
    // ignore: avoid_print
    print('RKEYS ${keys.toList()..sort()}');
    for (final f in g.me.falconry!.falcons) {
      final s = f.skill.toString();
      // ignore: avoid_print
      print('RHID skill $s in snapshot: ${text.contains(s)}');
    }
    for (final r in FalconRoute.values) {
      for (final l in FalconMarket.lots(g.state.world.seed, r, g.today)) {
        // ignore: avoid_print
        print('RHID lot ${l.key} value ${l.value} opening ${l.opening} in snapshot: ${text.contains('${l.value}')} skill ${l.skill} ${text.contains('${l.skill}')}');
      }
    }
  });
}
