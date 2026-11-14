// ignore_for_file: avoid_print
// Reviewer's own odds harness (T18). Independent of the worker's tool: each
// season is a NEW GAME on its own seed (not one game's years), set up by the
// player's own commands (BuyPermit, OrderGear, StartTrip), and every day
// passes through the full daily pipeline (advanceDays(1): the camp's supplies
// used by FalconrySystem, the auction's hammer the night after entry).
// Each bird netted is entered at the auction and its sale price read from the
// FalconFate(sold) event.
//
//   dart run tool/r_odds.dart <setup> <seasons> [seed0]
// setups: beginner | middle | top | hop (EndTrip/StartTrip across every
// trapping ground in each window) | remake (break and remake the camp at the
// same ground after each refusal-and-went or stoop) | spam (each command x5)
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/sim.dart';

int minuteIn(TrapWindow w, GameDay d) => switch (w) {
  TrapWindow.dawn => HuntSun.dawn(d) + 30,
  TrapWindow.midday => 720,
  TrapWindow.evening => HuntSun.sunset(d) - 30,
};

void main(List<String> args) {
  final setup = args[0];
  final seasons = int.parse(args[1]);
  final seed0 = args.length > 2 ? int.parse(args[2]) : 100000;
  final top = setup != 'beginner' && setup != 'middle';
  final ground = switch (setup) {
    'beginner' => Ground.sulayyil, // inland, south: the design's beginner
    'middle' => Ground.hail,
    _ => Ground.lith,
  };
  final windows = switch (setup) {
    'beginner' => [TrapWindow.dawn],
    'middle' => [TrapWindow.dawn],
    _ => TrapWindow.values,
  };
  final days = switch (setup) {
    'beginner' => 20,
    'middle' => 40,
    _ => 61,
  };
  final gear = <Gear, int>{
    Gear.pigeon: setup == 'beginner' ? 6 : (setup == 'middle' ? 12 : 20),
    Gear.pigeonNet: 1,
    if (top || setup == 'middle') Gear.binoculars: 1,
    if (top) Gear.birdNet: 1,
    if (top) Gear.mobileTent: 1,
  };
  var withBird = 0, withDear = 0, birds = 0;
  final prices = <int>[];
  var netSum = 0.0;
  final sw = Stopwatch()..start();
  for (var s = 0; s < seasons; s++) {
    final g = Game.create(
      seed: seed0 + s,
      playerName: 'r',
      farmName: 'r',
      region: Region.qassim,
      favourite: ColorCategory.wodh,
      startDay: GameDay.ofDate(DateTime.utc(2026, 9, 29)),
      startedAt: DateTime.utc(2026, 11, 14),
    );
    final me = g.me.id;
    Sim(g.state).pay(g.me, const Riyal(50000000), LedgerCategory.opening);
    final cash0 = g.me.cash.value;
    bool ok(Command c) => g.dispatch(c).ok;
    if (!ok(BuyPermit(me, PermitKind.trapping))) throw 'permit';
    for (final e in gear.entries) {
      if (!ok(OrderGear(me, e.key, e.value))) throw 'gear ${e.key}';
    }
    if (!ok(OrderGear(me, Gear.supplies, 60))) throw 'supplies';
    g.advanceDays(2); // to 1 October, the gear delivered
    if (!ok(StartTrip(me, TripKind.trapping, ground, days > 60 ? 60 : days))) {
      throw 'start';
    }
    var n = 0, dear = false;
    for (var day = 0; day < days; day++) {
      final today = g.today;
      if (PermitKind.trapping.seasonOn(today) == null) break;
      final grounds = setup == 'hop'
          ? [for (final x in Ground.values) if (x.trapping) x]
          : [ground];
      for (final w in windows) {
        final m = minuteIn(w, today);
        for (final gr in grounds) {
          if (setup == 'hop') {
            g.dispatch(EndTrip(me));
            if (!ok(StartTrip(me, TripKind.trapping, gr, 30))) continue;
          }
          final at = HuntAt.ground(gr);
          for (var again = 0; again < (setup == 'remake' ? 4 : 1); again++) {
            if (again > 0) {
              g.dispatch(EndTrip(me));
              if (!ok(StartTrip(me, TripKind.trapping, gr, 30))) break;
            }
            var seen = false;
            for (var k = 0; k < (setup == 'spam' ? 5 : 1); k++) {
              final r = g.dispatch(SpotFalcon(me, at, minute: m));
              seen = seen ||
                  r.events.whereType<TrapResult>().any(
                    (x) => x.outcome == TrapOutcome.inSight,
                  );
            }
            if (!seen) break;
            var netted = false;
            for (final lure in [Lure.pigeon, Lure.birdNet, Lure.pigeon,
                if (setup == 'spam') ...[Lure.pigeon, Lure.birdNet]]) {
              final res = g.dispatch(ReleaseLure(me, at, lure, minute: m));
              if (!res.ok) continue;
              final o = res.events.whereType<TrapResult>().single.outcome;
              if (o == TrapOutcome.netted) netted = true;
              if (o != TrapOutcome.refused && setup != 'spam') break;
            }
            if (netted) break;
          }
        }
      }
      for (final b in [...?g.me.falconry?.held]) {
        if (!g.me.falconry!.entered.contains(b.id)) {
          if (!ok(EnterTrapAuction(me, b.id))) throw 'enter';
        }
      }
      if (gear[Gear.pigeon]! >= 20 && g.me.hunt.has(Gear.pigeon) < 10) {
        ok(OrderGear(me, Gear.pigeon, 20 - g.me.hunt.has(Gear.pigeon)));
      }
      final ev = g.advanceDays(1);
      for (final e in ev.whereType<FalconFate>()) {
        if (e.fate == Fate.sold) {
          n++;
          prices.add(e.price!);
          if (e.price! >= 300000) dear = true;
        }
      }
    }
    // the last nights' sales
    final ev = g.advanceDays(2);
    for (final e in ev.whereType<FalconFate>()) {
      if (e.fate == Fate.sold) {
        n++;
        prices.add(e.price!);
        if (e.price! >= 300000) dear = true;
      }
    }
    if (n > 0) withBird++;
    if (dear) withDear++;
    birds += n;
    // the hunt's own money only (permit, gear, supplies, pigeons, upkeep,
    // sales): the ledger's hunting kinds
    var net = 0;
    for (final e in g.me.ledger) {
      switch (e.category) {
        case LedgerCategory.falconSale ||
              LedgerCategory.huntPermit ||
              LedgerCategory.falconGear ||
              LedgerCategory.falconUpkeep:
          net += e.amount.value;
        default:
      }
    }
    netSum += net;
    if (cash0 == 0) print('');
  }
  prices.sort();
  final mean = prices.isEmpty ? 0 : prices.reduce((a, b) => a + b) / prices.length;
  print('ROD $setup ${ground.label} days $days seasons $seasons '
      'withBird ${(withBird / seasons).toStringAsFixed(4)} '
      'birds/season ${(birds / seasons).toStringAsFixed(3)} '
      'withDear ${(withDear / seasons).toStringAsFixed(4)} '
      'dearShare ${(prices.where((p) => p >= 300000).length / (prices.isEmpty ? 1 : prices.length)).toStringAsFixed(3)} '
      'priceMean ${mean.round()} median ${prices.isEmpty ? 0 : prices[prices.length ~/ 2]} '
      'max ${prices.isEmpty ? 0 : prices.last} netMean ${(netSum / seasons).round()} '
      '(${sw.elapsed.inSeconds}s)');
}
