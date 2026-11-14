// Reviewer: the base's own v11 save (seed 7, 104 weeks) through the worker's codec.
import 'dart:convert';
import 'dart:io';
import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/persistence.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:test/test.dart';

void main() {
  test('base save migrates and plays a season with falcons', () {
    const codec = SaveCodec();
    final raw = File(Platform.environment['RSAVE']!).readAsStringSync();
    final l = codec.decode(raw) as Loaded;
    final g = Game(l.state);
    expect(l.migratedFrom, anyOf(11, 12));
    final unchanged = jsonEncode(g.state.toJson());
    expect(unchanged.contains('falconry'), isFalse);
    // a season on: to 1 Oct of the next year, with money
    g.advanceTo(GameDay.ofDate(DateTime.utc(g.today.date.year + (g.today.date.month >= 10 ? 1 : 0), 10, 1)));
    Sim(g.state).pay(g.me, const Riyal(3000000), LedgerCategory.opening);
    expect(g.dispatch(BuildFacility(g.me.id, Facility.falconRoom)).ok, isTrue);
    g.advanceDays(Balance.buildDays);
    expect(g.dispatch(BuyPermit(g.me.id, PermitKind.trapping)).ok, isTrue);
    for (final lot in FalconMarket.lots(g.state.world.seed, FalconRoute.exhibition, g.today)) {
      g.dispatch(BuyFalcon(g.me.id, lot.key, 1000000));
    }
    expect(g.dispatch(BuyPermit(g.me.id, PermitKind.hunting)).ok, isTrue);
    g.advanceDays(61);
    final back = (codec.decode(codec.encode(g.state)) as Loaded).state;
    expect(jsonEncode(back.toJson()), jsonEncode(g.state.toJson()));
    expect(checkInvariants(back), isEmpty);
    // ignore: avoid_print
    print('RMIG ok day ${g.today.value} falcons ${back.players.values.first.falconry!.falcons.length}');
  });
}
