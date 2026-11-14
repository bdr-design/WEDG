// Reviewer: hidden values across every view the phone/map reads (copy into
// marah_runtime/test/). Distinctive hidden numbers are planted and searched.
import 'dart:convert';
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:marah_runtime/marah_runtime.dart';
import 'package:marah_runtime/src/presenter.dart';
import 'package:test/test.dart';

Falcon mk(Game g, FalconHow how, {int? value, required double skill, bool keep = false}) => Falcon(
  id: g.state.world.ids.falcon(), name: 'x', species: FalconSpecies.passagePeregrine,
  female: true, hatched: 2026, how: how, on: g.today, ground: Ground.lith,
  lengthQ: 61, widthQ: 62, weightG: 1001, skill: skill, value: value,
  passport: keep ? '5555555555' : null, keep: keep, caredOn: g.today, dauDays: 28);

void main() {
  test('hidden', () {
    final g = Game.create(seed: 4242, playerName: 'p', farmName: 'f',
        region: Region.qassim, favourite: ColorCategory.wodh,
        startDay: GameDay.ofDate(DateTime.utc(2026, 10, 1)),
        startedAt: DateTime.utc(2026, 11, 14));
    Sim(g.state).pay(g.me, const Riyal(5000000), LedgerCategory.opening);
    g.dispatch(BuildFacility(g.me.id, Facility.falconRoom));
    g.advanceDays(Balance.buildDays);
    g.dispatch(BuyPermit(g.me.id, PermitKind.trapping));
    final h = g.me.hunt;
    h.held.add(mk(g, FalconHow.trapped, value: 345678, skill: 0.737));
    h.falcons.add(mk(g, FalconHow.trapped, value: 456789, skill: 0.643, keep: true));
    final lost = mk(g, FalconHow.trapped, value: 234567, skill: 0.581, keep: true)..where = FalconWhere.lost;
    h.falcons.add(lost);
    h.gear[Gear.supplies] = 10;
    g.dispatch(StartTrip(g.me.id, TripKind.trapping, Ground.lith, 5));
    final snap = jsonEncode(SnapshotJson.snapshot(Presenter(g.state, g.me.id).snapshot(1)));
    final cat = jsonEncode(falconCatalogOf(g.state, g.me.id));
    final card = jsonEncode(Trips.card(g, TripKind.trapping, Ground.lith, 5));
    final run = AwayRun(g, Trips.night(g)!);
    while (!run.done) { run.step(); }
    final away = jsonEncode(run.toJson());
    final all = '$snap\n$cat\n$card\n$away';
    final hidden = ['345678', '456789', '234567', '0.737', '0.643', '0.581', '73.7', '64.3', '58.1', '346', '457', '235'];
    for (final x in hidden) {
      // ignore: avoid_print
      print('RHID2 $x snapshot ${snap.contains(x)} catalog ${cat.contains(x)} card ${card.contains(x)} away ${away.contains(x)}');
    }
    for (final r in FalconRoute.values) {
      for (final l in FalconMarket.lots(g.state.world.seed, r, g.today)) {
        // ignore: avoid_print
        print('RHID2 lot ${l.key} worth ${l.value} in views ${all.contains('"${l.value}') || all.contains(':${l.value}') || all.contains(',${l.value}')} skill ${l.skill} ${all.contains('${l.skill}')}');
      }
    }
    final keys = RegExp(r'"([A-Za-z]+)":').allMatches(jsonEncode(SnapshotJson.snapshot(Presenter(g.state, g.me.id).snapshot(1))['falcons'])).map((m) => m[1]).toSet().toList()..sort();
    // ignore: avoid_print
    print('RHID2 keys $keys');
    // ignore: avoid_print
    print('RHID2 sizes snapshot ${snap.length} falcons ${jsonEncode(SnapshotJson.snapshot(Presenter(g.state, g.me.id).snapshot(1))['falcons']).length} catalog ${cat.length}');
  });
}
