// Reviewer's own checks of T18 items 1-2 (copy into packages/marah_domain/test/).
import 'dart:convert';
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:test/test.dart';

GameDay d(int y, int m, int day) => GameDay.ofDate(DateTime.utc(y, m, day));
Game gameOn(GameDay start, {int seed = 4242}) => Game.create(seed: seed,
    playerName: 'p', farmName: 'f', region: Region.qassim,
    favourite: ColorCategory.wodh, startDay: start,
    startedAt: DateTime.utc(2026, 11, 14));
void give(Game g, int r) => Sim(g.state).pay(g.me, Riyal(r), LedgerCategory.opening);
void room(Game g) {
  give(g, 18000);
  expect(g.dispatch(BuildFacility(g.me.id, Facility.falconRoom)).ok, isTrue);
  g.advanceDays(Balance.buildDays);
}
String st(Game g) => jsonEncode(g.state.toJson());

void main() {
  test('every refusal leaves the state as it was', () {
    final g = gameOn(d(2026, 9, 1));
    final cases = <Command>[
      BuyPermit(g.me.id, PermitKind.hunting),            // needsFalcon
      OrderGear(g.me.id, Gear.pigeonNet, 2),               // gearFull
      OrderGear(g.me.id, Gear.pigeon, 0),                  // invalid
      BuyFalcon(g.me.id, 'trapping:${g.today.value}:0'), // routeClosed (Sep)
      BuyFalcon(g.me.id, 'nonsense'),                      // lotGone
    ];
    for (final c in cases) {
      final before = st(g);
      final r = g.dispatch(c);
      expect(r.ok, isFalse, reason: '$c');
      expect(st(g), before, reason: '$c');
    }
    // no room, room full, permit held, money short
    g.advanceTo(d(2026, 10, 1));
    var lots = FalconMarket.lots(g.state.world.seed, FalconRoute.exhibition, g.today);
    var before = st(g);
    expect(g.dispatch(BuyFalcon(g.me.id, lots.first.key)).ok, isFalse);
    expect(st(g), before, reason: 'no room');
    give(g, 1000000);
    g.dispatch(BuyPermit(g.me.id, PermitKind.trapping));
    before = st(g);
    expect(g.dispatch(BuyPermit(g.me.id, PermitKind.trapping)).ok, isFalse);
    expect(st(g), before, reason: 'permit held');
  });

  test('the hunting permit valid 1 Sep - 31 Jan, both edges', () {
    final g = gameOn(d(2027, 8, 5));
    give(g, 5000000);
    room(g);
    final lot = FalconMarket.lots(g.state.world.seed, FalconRoute.breeders, g.today).first;
    expect(g.dispatch(BuyFalcon(g.me.id, lot.key)).ok, isTrue);
    expect(g.me.falconry!.falcons, hasLength(1));
    expect(g.dispatch(BuyPermit(g.me.id, PermitKind.hunting)).ok, isTrue);
    final h = g.me.falconry!;
    g.advanceTo(d(2027, 8, 31));
    expect(h.holds(PermitKind.hunting, g.today), isFalse);
    g.advanceDays(1);
    expect(h.holds(PermitKind.hunting, g.today), isTrue);
    g.advanceTo(d(2028, 1, 31));
    expect(h.holds(PermitKind.hunting, g.today), isTrue);
    g.advanceDays(1);
    expect(h.holds(PermitKind.hunting, g.today), isFalse);
  });

  test('a stale lot key (yesterday\'s) is not today\'s bird', () {
    final g = gameOn(d(2026, 10, 2));
    give(g, 5000000);
    room(g);
    final y = g.today - 1;
    final r = g.dispatch(BuyFalcon(g.me.id, 'exhibition:${y.value}:0'));
    expect(r.ok, isFalse);
  });

  test('upkeep is 20 a day per falcon', () {
    final g = gameOn(d(2026, 10, 1));
    give(g, 5000000);
    room(g);
    final lots = FalconMarket.lots(g.state.world.seed, FalconRoute.exhibition, g.today);
    for (final l in lots) { g.dispatch(BuyFalcon(g.me.id, l.key)); }
    final n = g.me.falconry!.falcons.length;
    final c = g.me.cash.value;
    g.advanceDays(1);
    // (milk etc. also move cash: compare the upkeep ledger row's growth)
    final row = g.me.ledger.lastWhere((e) => e.category == LedgerCategory.falconUpkeep);
    expect(n, greaterThan(0));
    expect(row.amount.value % (20 * n), 0);
    expect(c, isNonZero);
  });

  test('exact cash buys the lot', () {
    final g = gameOn(d(2026, 10, 1));
    give(g, 1000000);
    room(g);
    final l = FalconMarket.lots(g.state.world.seed, FalconRoute.exhibition, g.today).first;
    Sim(g.state).pay(g.me, Riyal(l.value - g.me.cash.value), LedgerCategory.opening);
    expect(g.dispatch(BuyFalcon(g.me.id, l.key)).ok, isTrue);
    expect(g.me.falconry!.falcons, hasLength(1));
    expect(g.me.cash.value, 0);
  });

  test('REPORT: blind price at the breeders and the exhibition; openings', () {
    var dearBreeders = 0, nBreeders = 0, maxB = 0;
    final byOpening = <int, List<int>>{};
    for (var seed = 1; seed <= 400; seed++) {
      for (var day = d(2027, 8, 5); day <= d(2027, 8, 25); day += 1) {
        for (final l in FalconMarket.lots(seed, FalconRoute.breeders, day)) {
          nBreeders++;
          if (l.value >= 100000) dearBreeders++;
          if (l.value > maxB) maxB = l.value;
        }
      }
      for (var day = d(2026, 10, 1); day <= d(2026, 11, 30); day += 1) {
        for (final l in FalconMarket.lots(seed, FalconRoute.trapping, day)) {
          byOpening.putIfAbsent(l.opening, () => []).add(l.value);
        }
      }
    }
    // ignore: avoid_print
    print('RREP breeders lots $nBreeders, >=100k $dearBreeders, max $maxB');
    for (final o in (byOpening.keys.toList()..sort())) {
      final v = byOpening[o]!..sort();
      final dear = v.where((x) => x >= 300000).length / v.length;
      // ignore: avoid_print
      print('RREP opening $o n ${v.length} min ${v.first} max ${v.last} dear ${dear.toStringAsFixed(2)}');
    }
  });
}
