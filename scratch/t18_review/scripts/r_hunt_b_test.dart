// Reviewer's own checks of T18 (final build). Copy into
// packages/marah_domain/test/ and run there.
import 'dart:convert';

import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:test/test.dart';

GameDay d(int y, int m, int day) => GameDay.ofDate(DateTime.utc(y, m, day));
Game gameOn(GameDay start, {int seed = 4242}) => Game.create(
  seed: seed,
  playerName: 'p',
  farmName: 'f',
  region: Region.qassim,
  favourite: ColorCategory.wodh,
  startDay: start,
  startedAt: DateTime.utc(2026, 11, 14),
);
void give(Game g, int r) =>
    Sim(g.state).pay(g.me, Riyal(r), LedgerCategory.opening);
String st(Game g) => jsonEncode(g.state.toJson());
Game copy(Game g) => Game(GameState.fromJson(
      jsonDecode(jsonEncode(g.state.toJson())) as Map<String, Object?>,
    ));
void hand(Game g, Gear x, int n) => g.me.hunt.gear[x] = n;

Game trapper({int seed = 4242}) {
  final g = gameOn(d(2026, 9, 26), seed: seed);
  give(g, 3000000);
  g.dispatch(BuildFacility(g.me.id, Facility.falconRoom));
  g.dispatch(BuyPermit(g.me.id, PermitKind.trapping));
  g.advanceTo(d(2026, 10, 1));
  for (final x in [Gear.pigeonNet, Gear.birdNet, Gear.binoculars, Gear.mobileTent]) {
    hand(g, x, 1);
  }
  hand(g, Gear.pigeon, 20);
  hand(g, Gear.supplies, 60);
  return g;
}

Falcon falcon(Game g, {double skill = 0.6}) {
  final f = Falcon(
    id: g.state.world.ids.falcon(),
    name: 'غيث',
    species: FalconSpecies.saker,
    female: true,
    hatched: 2026,
    how: FalconHow.bought,
    on: g.today,
    route: FalconRoute.breeders,
    price: 19000,
    lengthQ: 66,
    widthQ: 66,
    weightG: 1100,
    passport: '1234567890',
    skill: skill,
    dauDays: HuntBalance.dauDaysNeeded,
    caredOn: g.today,
  );
  g.me.hunt.falcons.add(f);
  return f;
}

void main() {
  test('every refusal I can reach leaves the state as it was, no fine', () {
    final g = trapper();
    final f = falcon(g);
    final me = g.me.id;
    void none(Command c, String reason) {
      final before = st(g);
      final r = g.dispatch(c);
      expect(r.ok, isFalse, reason: reason);
      expect(st(g), before, reason: reason);
    }

    none(SpotFalcon(me, const HuntAt.ground(Ground.lith), minute: 400), 'not on trip');
    none(SpotFalcon(me, const HuntAt.off(HuntOff.farm), minute: 400), 'off ground');
    none(ReleaseLure(me, const HuntAt.ground(Ground.lith), Lure.pigeon, minute: 400), 'not on trip lure');
    none(StartTrip(me, TripKind.trapping, Ground.nafudEdge, 3), 'trap on a hunting ground');
    none(StartTrip(me, TripKind.trapping, Ground.lith, 0), 'too far for a day');
    none(StartTrip(me, TripKind.falconry, Ground.nafudEdge, 0), 'no hunting permit');
    none(CastFalcon(me, f.id, const HuntAt.off(HuntOff.farm), minute: 700), 'near farm');
    none(CastFalcon(me, f.id, const HuntAt.off(HuntOff.coast), minute: 700), 'coast');
    none(CastFalcon(me, f.id, const HuntAt.off(HuntOff.reserve), minute: 700), 'reserve');
    none(EnterTrapAuction(me, f.id), 'not held');
    none(ReleaseFalcon(me, f.id), 'bought not freed');
    none(SearchFalcon(me, f.id), 'not lost');
    none(EndTrip(me), 'no trip');
    none(MoveCamp(me, Ground.lith), 'no trip move');
    expect(g.dispatch(StartTrip(me, TripKind.trapping, Ground.lith, 10)).ok, isTrue);
    none(SpotFalcon(me, const HuntAt.ground(Ground.lith), minute: 100), 'night');
    none(SpotFalcon(me, const HuntAt.ground(Ground.jazan), minute: 400), 'other ground');
    none(StartTrip(me, TripKind.trapping, Ground.lith, 10), 'on trip');
    hand(g, Gear.birdNet, 0);
    g.advanceTo(d(2026, 12, 1));
    none(SpotFalcon(me, const HuntAt.ground(Ground.lith), minute: 500), 'season over');
  });

  test('N3: a camp day jumped by the away call equals a played day', () {
    final a = trapper();
    a.dispatch(StartTrip(a.me.id, TripKind.trapping, Ground.hamad, 9));
    falcon(a);
    final b = copy(a);
    a.advanceDays(1);
    final run = AwayRun(b, Trips.night(b)!);
    while (!run.done) {
      run.step();
    }
    expect(st(b), st(a));
  });

  test('FINDING: the drive is not charged: trap at Jazan (1,324 km) the '
      'minute the trip starts, home the minute it ends', () {
    final g = trapper();
    final me = g.me.id;
    final day = g.today;
    expect(g.dispatch(StartTrip(me, TripKind.trapping, Ground.jazan, 5)).ok, isTrue);
    final r = g.dispatch(SpotFalcon(me, const HuntAt.ground(Ground.jazan), minute: 400));
    expect(r.ok, isTrue, reason: 'trapping 1,324 km away the same minute');
    expect(g.dispatch(EndTrip(me)).ok, isTrue);
    expect(g.dispatch(StartTrip(me, TripKind.trapping, Ground.wajh, 5)).ok, isTrue);
    expect(g.dispatch(SpotFalcon(me, const HuntAt.ground(Ground.wajh), minute: 401)).ok, isTrue);
    expect(g.today, day);
  });

  test('FINDING: casts with no trip are not limited to 3 a day; one hour '
      'gives the same draw, and each catch is counted', () {
    final g = gameOn(d(2026, 9, 26));
    give(g, 3000000);
    g.dispatch(BuildFacility(g.me.id, Facility.falconRoom));
    g.advanceTo(d(2026, 10, 1));
    final f = falcon(g, skill: 0.9);
    expect(g.dispatch(BuyPermit(g.me.id, PermitKind.hunting)).ok, isTrue);
    var ok = 0;
    for (var i = 0; i < 10; i++) {
      final r = g.dispatch(CastFalcon(g.me.id, f.id, const HuntAt.ground(Ground.nafudEdge), minute: 700));
      if (r.ok) ok++;
      if (f.where == FalconWhere.lost) break;
    }
    // ignore: avoid_print
    print('RFIND casts accepted $ok, flights ${f.flights}, taken ${f.taken}');
    expect(ok, greaterThan(TrapOdds.flightsADay));
  });

  test('save-scum: a day\'s trapping replayed from a copy gives the same', () {
    var differ = 0, total = 0;
    for (var seed = 1; seed <= 300; seed++) {
      final g = trapper(seed: seed);
      g.dispatch(StartTrip(g.me.id, TripKind.trapping, Ground.lith, 30));
      for (var day = 0; day < 20; day++) {
        final c = copy(g);
        List<String> play(Game x, List<Lure> lures) {
          final out = <String>[];
          for (final w in [400, 720, HuntSun.sunset(x.today) - 30]) {
            final at = const HuntAt.ground(Ground.lith);
            final s = x.dispatch(SpotFalcon(x.me.id, at, minute: w));
            out.add(s.events.whereType<TrapResult>().single.outcome.name);
            for (final l in lures) {
              final r = x.dispatch(ReleaseLure(x.me.id, at, l, minute: w));
              if (r.ok) out.add(r.events.whereType<TrapResult>().single.outcome.name);
            }
          }
          return out;
        }
        final a = play(g, [Lure.pigeon, Lure.birdNet, Lure.pigeon]);
        final b = play(c, [Lure.pigeon, Lure.birdNet, Lure.pigeon]);
        total++;
        if (a.join() != b.join()) differ++;
        g.advanceDays(1);
      }
    }
    expect(differ, 0, reason: 'of $total days');
  });

  test('REPORT: openings against the worth, by band', () {
    final byBand = <int, List<int>>{};
    for (var seed = 1; seed <= 400; seed++) {
      for (var day = d(2026, 10, 1); day <= d(2026, 11, 30); day += 1) {
        for (final l in FalconMarket.lots(seed, FalconRoute.trapping, day)) {
          byBand.putIfAbsent(l.opening ~/ 10000 * 10000, () => []).add(l.value);
        }
      }
    }
    for (final o in (byBand.keys.toList()..sort())) {
      final v = byBand[o]!..sort();
      final dear = v.where((x) => x >= 300000).length / v.length;
      // ignore: avoid_print
      print('RREP opening ${o ~/ 1000}k-${o ~/ 1000 + 9}k n ${v.length} '
          'min ${v.first} median ${v[v.length ~/ 2]} dear ${dear.toStringAsFixed(2)}');
    }
  });

  test('the lot lost to a ceiling below its worth: told, gone', () {
    final g = gameOn(d(2026, 10, 1));
    give(g, 3000000);
    g.dispatch(BuildFacility(g.me.id, Facility.falconRoom));
    g.advanceDays(Balance.buildDays);
    final l = FalconMarket.lots(g.state.world.seed, FalconRoute.exhibition, g.today).first;
    final cash = g.me.cash.value;
    final r = g.dispatch(BuyFalcon(g.me.id, l.key, l.value - 1));
    expect(r.ok, isTrue);
    expect(r.events.whereType<FalconLotLost>().single.price, l.value);
    expect(g.me.cash.value, cash);
    expect(g.dispatch(BuyFalcon(g.me.id, l.key, l.value)).ok, isFalse);
    final l2 = FalconMarket.lots(g.state.world.seed, FalconRoute.exhibition, g.today)[1];
    expect(g.dispatch(BuyFalcon(g.me.id, l2.key, l2.value)).ok, isTrue);
    expect(g.me.cash.value, cash - l2.value);
  });

  test('FINDING?: الدعو from a camp 843 km away', () {
    final g = trapper();
    final f = falcon(g);
    f.dauDays = 10;
    g.dispatch(StartTrip(g.me.id, TripKind.trapping, Ground.hamad, 20));
    for (var i = 0; i < 5; i++) {
      final run = AwayRun(g, Trips.night(g)!);
      while (!run.done) {
        run.step();
      }
    }
    final r = g.dispatch(CareFalcons(g.me.id));
    // ignore: avoid_print
    print('RFIND care from camp ok=${r.ok} dau ${f.dauDays}');
  });
}
