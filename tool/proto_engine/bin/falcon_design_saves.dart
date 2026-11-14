// Saves for the phone's hunting season (task T18 part B): the views of «نادي الصقور» and «تصريح الصيد» shot from
// real games on the engine (design/ui/phone_falcon_engine.cjs and the page harness). Every state is PLAYED by the
// engine's own commands and days; the one thing granted is money (LedgerCategory.opening, as the other design saves
// do: a new game has 20,000, and a falcon at the trapping auction is from about 50,000).
//
// Run `dart run bin/falcon_design_saves.dart <out folder> [seed]` in tool/proto_engine. It writes:
//   buyer.json        1 October, 400,000 granted, the falcons' room built at once (BuildFacility now: the rush)
//   noroom.json       1 October, 400,000 granted, no room
//   held.json         a trapping camp played day by day on a trapping ground (permit, gear ordered and delivered,
//                     each window looked at and the pigeon then the bird net let go) till a sellable peregrine is in
//                     the net; the camp broken; at the farm, no room yet
//   held_room.json    the same game, the room built at once after (a free place)
//   held_full.json    the same game, the room built and four falcons bought at the auctions (the room full)
//   entered.json      held_room.json with the bird entered for tonight's auction
//   sold.json         entered.json a day on: the hammer fell (falconFacts' news)
//   close.json        held.json on 30 November, the auction's last night, the bird still held
//   closed.json       close.json a day on: the bird freed at the close (news)
//   mine.json         held_full.json's falcons: الدعو done on some days, a week of it left undone
// The page opens one from localStorage (the harness), its clock shifted so it runs on from the save's day.
import 'dart:io';

import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/testing.dart';

late DateTime now;

Game newGame(int seed) => Game.create(
  seed: seed,
  playerName: 'اللاعب',
  farmName: 'العزبة',
  region: Region.qassim,
  favourite: ColorCategory.wodh,
  startedAt: now,
);

void must(Result r, String what) {
  if (!r.ok) throw StateError('$what refused: $r');
}

void write(Game g, String dir, String name) {
  g.state
    ..clockShiftMs = -g.today.daysSince(g.state.startedOn) * 86400000 ~/ 7
    ..lastSeenUtcMs = now.millisecondsSinceEpoch;
  File('$dir/$name').writeAsStringSync(const SaveCodec().encode(g.state));
  final h = g.me.falconry;
  stdout.writeln(
    '$name: ${g.today.date.toIso8601String().substring(0, 10)} cash ${g.me.cash.value} '
    'falcons ${h?.falcons.length ?? 0} held ${h?.held.length ?? 0} '
    'invariants ${checkInvariants(g.state)}',
  );
}

Game copy(Game g) => Game(GameState.fromJson(g.state.toJson()));

/// Stores filled so the herd lives through the days played unattended.
void stock(Game g) => g.me.farm
  ..storeKg = 100000
  ..tankL = 200000
  ..barleyKg = 40000
  ..alfalfaKg = 40000
  ..waterL = 190000;

/// Buys today's lots at any auction open with a ceiling well above, day by day, till he has [n] falcons.
void buyFalcons(Game g, int n) {
  final me = g.me.id;
  for (var day = 0; g.me.hunt.falcons.length < n && day < 90; day++) {
    for (final r in FalconRoute.values) {
      if (!r.openOn(g.today)) continue;
      for (final l in FalconMarket.lots(g.state.world.seed, r, g.today)) {
        if (g.me.hunt.falcons.length >= n) break;
        // (the price granted for it: his balance as it was before)
        final before = g.me.cash.value;
        grant(g, 1000000);
        must(g.dispatch(BuyFalcon(me, l.key, 1000000)), 'BuyFalcon');
        grant(g, before - g.me.cash.value);
      }
    }
    if (g.me.hunt.falcons.length < n) g.advanceDays(1);
  }
}

void main(List<String> args) {
  now = DateTime.now().toUtc();
  final dir = args.first;
  final seed = args.length > 1 ? int.parse(args[1]) : 4242;
  Directory(dir).createSync(recursive: true);

  // ---- the buyer: a room at once, money for a bird
  final b = newGame(seed);
  final me = b.me.id;
  grant(b, 400000);
  must(
    b.dispatch(BuildFacility(me, Facility.falconRoom, now: true)),
    'the room now',
  );
  write(b, dir, 'buyer.json');
  final nr = newGame(seed);
  grant(nr, 400000);
  write(nr, dir, 'noroom.json');

  // ---- a trapping camp played till a sellable bird is in the net (most well-equipped seasons trap one: on a seed
  // whose season does not, the next seed is played, and named)
  Game? got;
  for (var s = seed; got == null && s < seed + 30; s++) {
    got = camp(s);
  }
  final g = got!;
  final gm = g.me.id;
  if (g.me.hunt.trip != null) must(g.dispatch(EndTrip(gm)), 'EndTrip');
  write(g, dir, 'held.json');

  final room = copy(g);
  grant(room, 40000);
  must(
    room.dispatch(BuildFacility(gm, Facility.falconRoom, now: true)),
    'the room now',
  );
  write(room, dir, 'held_room.json');

  final full = copy(room);
  buyFalcons(full, 4);
  write(full, dir, 'held_full.json');

  final entered = copy(room);
  must(
    entered.dispatch(EnterTrapAuction(gm, entered.me.hunt.held.single.id)),
    'EnterTrapAuction',
  );
  write(entered, dir, 'entered.json');
  entered.advanceDays(1);
  write(entered, dir, 'sold.json');

  final close = copy(g);
  close.advanceTo(GameDay.ofDate(DateTime.utc(close.today.date.year, 11, 30)));
  write(close, dir, 'close.json');
  close.advanceDays(1);
  write(close, dir, 'closed.json');

  // his falcons: الدعو done some days, then a week left undone
  final mine = copy(full);
  for (var i = 0; i < 9; i++) {
    mine.dispatch(CareFalcons(gm));
    mine.advanceDays(1);
  }
  mine.advanceDays(6);
  write(mine, dir, 'mine.json');
}

/// A trapping camp on [seed]'s new game, played day by day; the game once a sellable bird is in the net, or null.
Game? camp(int seed) {
  final g = newGame(seed);
  final me = g.me.id;
  stock(g);
  grant(g, 60000);
  must(g.dispatch(BuyPermit(me, PermitKind.trapping)), 'the trapping permit');
  for (final (x, n) in [
    (Gear.pigeon, 20),
    (Gear.pigeonNet, 1),
    (Gear.birdNet, 1),
    (Gear.binoculars, 1),
    (Gear.supplies, 60),
  ]) {
    must(g.dispatch(OrderGear(me, x, n)), 'OrderGear $x');
  }
  g.advanceDays(1); // delivered next day
  const ground = Ground.lith;
  must(g.dispatch(StartTrip(me, TripKind.trapping, ground, 59)), 'StartTrip');
  const at = HuntAt.ground(ground);
  var nights = 0;
  while (g.me.hunt.held.isEmpty && g.me.hunt.trip != null) {
    final day = g.today;
    for (final minute in [
      HuntSun.dawn(day) + 40,
      720,
      HuntSun.sunset(day) - 30,
    ]) {
      g.dispatch(SpotFalcon(me, at, minute: minute));
      for (var i = 0; i < 3 && g.me.hunt.held.isEmpty; i++) {
        final pigeon = g.me.hunt.has(Gear.pigeon) > 0 && i != 1;
        final r = g.dispatch(
          ReleaseLure(
            me,
            at,
            pigeon ? Lure.pigeon : Lure.birdNet,
            minute: minute,
          ),
        );
        final o = r.events.whereType<TrapResult>().firstOrNull?.outcome;
        if (o != TrapOutcome.refused) break;
      }
      if (g.me.hunt.held.isNotEmpty) break;
    }
    if (g.me.hunt.held.isNotEmpty) break;
    final plan = Trips.night(g);
    if (plan == null) break;
    final run = AwayRun(g, plan);
    while (!run.done) {
      run.step();
    }
    nights++;
    if (run.stop?.kind == AwayStopKind.extra &&
        g.me.hunt.trip != null &&
        run.stop?.extra != 'tripEnd') {
      // a stop the camp cannot go on through (supplies out, the season's end)
      break;
    }
  }
  if (g.me.hunt.held.isEmpty) {
    stdout.writeln('seed $seed: no sellable bird in $nights nights');
    return null;
  }
  stdout.writeln(
    'seed $seed: netted on night $nights: ${g.me.hunt.held.single.name}',
  );
  return g;
}
