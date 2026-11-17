import 'dart:collection';

import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/handlers/falconry.dart' show gearRoom;
import 'package:marah_domain/testing.dart';

import 'commands_json.dart';

/// The scripted bot plays a fixed seed, and every [every] weeks the whole
/// state is written in a canonical form and hashed. bin/same_seed.dart prints
/// these lines on the Dart VM and compiled to JavaScript; CI fails if the two
/// differ, because the prototype's engine must be the app's, day for day.
/// [end] gets the game after the last week.
Iterable<String> sameSeedLines({
  int seed = 7,
  int weeks = 104,
  int every = 4,
  void Function(Game game)? end,
  bool rush = true,
  bool legacyState = false,
}) sync* {
  final game = Game.create(
    seed: seed,
    playerName: 'اللاعب',
    farmName: 'العزبة',
    region: Region.qassim,
    favourite: ColorCategory.majaheem,
    startedAt: DateTime.utc(2026, 11, 1),
  );
  // the old start's money (SAR 600,000), so the rich farm's paths run too:
  // a bull bought, festivals entered and withdrawn from
  grant(game, 580000);
  final bot = Bot(game);
  var extras = 0;
  final done = SplayTreeMap<String, int>();
  for (var w = 0; ; w++) {
    if (w % every == 0 || w == weeks) {
      yield 'week $w day ${game.today.value} cash ${game.me.cash.value} '
          'commands ${bot.commands} refused ${bot.refused} extras $extras '
          '${legacyState ? stateLineV9(game.state) : stateLine(game.state)}';
    }
    if (w == weeks) {
      yield 'extras ${[for (final e in done.entries) '${e.key} ${e.value}'].join(', ')}';
      end?.call(game);
      return;
    }
    extras += _extras(game, w, done, rush: rush);
    bot.week();
  }
}

/// The commands the bot never sends, so the check runs them too: the feed
/// plan changed, the calves' share of the milk, a camel renamed, a camel listed and its offers declined, then
/// taken off the market, a female put to the farm's own bull, an entry
/// withdrawn, a camel secretly treated. Returns how many went through, and counts them by kind in
/// [done].
int _extras(Game game, int week, Map<String, int> done, {bool rush = true}) {
  final me = game.me.id;
  var ok = 0;
  void send(Command c) {
    if (!game.dispatch(c).ok) return;
    ok++;
    final kind = commandToJson(c)['type']! as String;
    done[kind] = (done[kind] ?? 0) + 1;
  }

  // a round's day the bot's last week ended on, told hour by hour (as the
  // engine does by the clock), and the treatment man's messages read and the
  // findings told, as the phone does
  if (game.nextTelling != null) {
    for (final m in Balance.stageMinutes) {
      if (game.tellTo(m).isNotEmpty || m == Balance.stageMinutes.last) {
        done['tellTo'] = (done['tellTo'] ?? 0) + 1;
      }
    }
  }
  if (week % 3 == 0 && game.me.dealer.any((m) => !m.read)) {
    send(ReadMessages(me));
  }
  if (game.me.untold.isNotEmpty) send(MarkFindingsTold(me, 1));
  var v = GameView(game.state, me);
  if (week % 8 == 0) {
    send(
      SetFeedPlan(me, week % 16 == 0 ? FeedPlan.premium : FeedPlan.standard),
    );
  }
  // the calves' share of the milk, each of the three in turn
  if (week % 6 == 3) {
    send(SetCalfShare(me, CalfShare.values[(week ~/ 6) % 3]));
  }
  if (week % 4 == 1 && v.herd.isNotEmpty) {
    send(RenameCamel(me, v.herd.first.id, 'ناقة $week'));
  }
  // one camel on the market for four weeks at its dearer estimate: offers come,
  // and every one is declined, then it is taken off
  if (week % 8 == 0) {
    for (final c in v.herd) {
      if (v.canSell(c.id) == null && v.listingOf(c.id) == null) {
        send(ListForSale(me, c.id, c.estimate.$2.value));
        break;
      }
    }
  } else if (week % 8 == 4) {
    for (final l in v.myListings) {
      send(CancelListing(me, l.id));
    }
  }
  v = GameView(game.state, me);
  for (final l in v.myListings) {
    for (final o in v.offersOn(l.id)) {
      send(DeclineOffer(me, o.id));
    }
  }
  // the farm's own bull: bought grown when there is none, then used
  if (v.breedingSeason) {
    bool serves(CamelView c) => c.sex == Sex.male && v.canServe(c.id) == null;
    if (!v.herd.any(serves) && v.me.cash.value > 100000) {
      final bulls =
          v.market
              .where(
                (l) =>
                    l.camel.sex == Sex.male &&
                    l.camel.ageDays > 6 * 365 &&
                    l.askPrice.value < v.me.cash.value * 0.4,
              )
              .toList()
            ..sort((a, b) => a.askPrice.value.compareTo(b.askPrice.value));
      if (bulls.isNotEmpty) send(BuyListing(me, bulls.first.id));
      v = GameView(game.state, me);
    }
    final bull = v.herd.where(serves).firstOrNull;
    if (bull != null) {
      for (final f in v.herd.where((c) => c.sex == Sex.female)) {
        if (v.canBreed(f.id) == null) {
          send(MateWithOwnBull(me, f.id, bull.id));
          break;
        }
      }
    }
  }
  // secret treatments after the run's last festival (Tabuk's, June 2028),
  // so the bot's festivals are not cut short by a ban, while the treatment,
  // its wearing off and a catch outside the festivals run on both platforms
  if (week >= 86 && week % 4 == 2 && v.herd.isNotEmpty) {
    send(Tamper(me, v.herd.last.id, TamperKind.values[week % 7], 1 + week % 3));
  }
  // the rush and being away (T15), so their paths run on both platforms: a
  // pen built now, a camel rushed home, the standing orders and the vet's
  // contract switched on and off, a short day's tanker, and a week away
  if (rush && week == 6) send(BuildFacility(me, Facility.pen, now: true));
  if (rush && week == 12) {
    send(SetStandingOrder(me, StandingOrder.water, on: true));
    send(SetStandingOrder(me, StandingOrder.feed, on: true));
    send(SignVetContract(me));
  }
  if (rush && week == 40) send(CancelVetContract(me));
  if (rush && week == 60) {
    send(SetStandingOrder(me, StandingOrder.feed, on: false));
  }
  for (final c in v.herd) {
    if (rush && c.onTheWay) send(RushTruck(me, c.id, hour: week % 24));
  }
  if (rush && (game.me.farm.today?.waterShort ?? false)) {
    send(OrderSupply(me, Supply.water, 1, tanker: Tanker.small, now: true));
  }
  if (rush && week == 101) {
    final run = AwayRun(game, AwayPlan(game.today + 7));
    while (!run.done) {
      run.step();
    }
    done['away'] = (done['away'] ?? 0) + 1;
  }
  if (week % 5 == 2) {
    for (final f in v.festivals.where((f) => f.registrationOpen(v.today))) {
      for (final r in f.rounds) {
        final mine = r.myEntries;
        if (mine.isNotEmpty) {
          send(WithdrawEntry(me, f.id, r.id, mine.first.camelId));
          return ok;
        }
      }
    }
  }
  return ok;
}

/// The state's canonical length and hash, the part of a line that a save
/// read back on the other platform must reproduce (bin/read_save.dart).
String stateLine(GameState state) {
  final text = canonicalJson(state.toJson());
  return 'length ${text.length} hash ${textHash(text)}';
}

/// [stateLine] of the state as a save before the rush (v9) holds it: the
/// farm's day record, which every day now writes, left out (the old game's
/// check: test/old_game_test.dart).
String stateLineV9(GameState state) {
  final j = state.toJson();
  for (final p in j['players']! as List<Object?>) {
    ((p! as Map<String, Object?>)['farm']! as Map<String, Object?>).remove(
      'today',
    );
  }
  final text = canonicalJson(j);
  return 'length ${text.length} hash ${textHash(text)}';
}

/// JSON with numbers written the same way on both platforms: each number's
/// shortest text that reads back the same, without a trailing `.0` (the VM
/// writes the double 1.0 as `1.0` and 2e20 as `200000000000000000000.0`,
/// JavaScript without the `.0`; otherwise the two agree, the test checks a
/// spread of values on both). Key order is kept: it is part of the state.
String canonicalJson(Object? v) {
  final b = StringBuffer();
  void write(Object? v) {
    switch (v) {
      case null:
        b.write('null');
      case bool():
        b.write(v);
      case num():
        final t = '$v';
        b.write(t.endsWith('.0') ? t.substring(0, t.length - 2) : t);
      case String():
        b.write('"');
        for (final u in v.codeUnits) {
          if (u == 0x22 || u == 0x5C) {
            b.write(r'\');
            b.writeCharCode(u);
          } else if (u < 0x20) {
            b.write(r'\u');
            b.write(u.toRadixString(16).padLeft(4, '0'));
          } else {
            b.writeCharCode(u);
          }
        }
        b.write('"');
      case List():
        b.write('[');
        for (var i = 0; i < v.length; i++) {
          if (i > 0) b.write(',');
          write(v[i]);
        }
        b.write(']');
      case Map():
        b.write('{');
        var first = true;
        for (final e in v.entries) {
          if (!first) b.write(',');
          first = false;
          write('${e.key}');
          b.write(':');
          write(e.value);
        }
        b.write('}');
      default:
        throw ArgumentError('not JSON: ${v.runtimeType}');
    }
  }

  write(v);
  return b.toString();
}

/// A 30-bit rolling hash of the UTF-16 code units, exact in JavaScript too
/// (every product stays far below 2^53).
int textHash(String s) {
  var h = 0;
  for (final u in s.codeUnits) {
    h = (h * 31 + u) & 0x3FFFFFFF;
  }
  return h;
}

/// The hunting season's paths (task T18), on a game of their own so the main
/// run above stays the base's. The seed and the grounds are chosen so that
/// every path runs (the reviewer's finding 8): birds netted on the coast, one
/// kept, one entered and sold, one left neither and set free at the
/// auction's close; birds released by their lines; the camp's supplies out
/// and a falcon left at the farm stopping a night; الدعو; a trip of days at
/// the estate with casts till a falcon is lost and looked for with its
/// tracker; the kept peregrine set free in February; and a refusal of each
/// kind the commands can meet. A line at each stage, on both platforms;
/// [covered] (when given) collects what ran, for the test that each path
/// did (test/proto_engine_test.dart).
Iterable<String> huntLines({int seed = huntSeed, Set<String>? covered}) sync* {
  final g = Game.create(
    seed: seed,
    playerName: 'اللاعب',
    farmName: 'العزبة',
    region: Region.qassim,
    favourite: ColorCategory.majaheem,
    startDay: GameDay.ofDate(DateTime.utc(2026, 9, 20)),
    startedAt: DateTime.utc(2026, 11, 1),
  );
  grant(g, 5000000);
  final me = g.me.id;
  final seen = covered ?? <String>{};
  var ok = 0, refused = 0;
  void note(Iterable<DomainEvent> events) {
    for (final e in events) {
      switch (e) {
        case TrapResult(:final outcome, :final species):
          seen.add('trap:${outcome.name}');
          if (outcome == TrapOutcome.released) {
            seen.add(
              species == FalconSpecies.mountainPeregrine ||
                      species == FalconSpecies.lanner
                  ? 'released:resident'
                  : 'released:${species!.name}',
            );
          }
        case CastResult(:final outcome):
          seen.add('cast:${outcome.name}');
        case FalconFate(:final fate):
          seen.add('fate:${fate.name}');
          if (fate == Fate.found || fate == Fate.notFound) seen.add('searched');
        default:
          break;
      }
    }
  }

  void send(Command c) {
    final r = g.dispatch(c);
    note(r.events);
    if (r is Err) {
      refused++;
      if (r.error.code == ErrorCode.huntRefused) {
        seen.add('refused:${r.error.params['reason']}');
      }
    } else {
      ok++;
    }
  }

  void days(int n) => note(g.advanceDays(n));
  String line(String what) {
    final text = canonicalJson(g.state.toJson());
    return 'hunt $what day ${g.today.value} cash ${g.me.cash.value} '
        'ok $ok refused $refused length ${text.length} hash ${textHash(text)}';
  }

  /// The trip's legs by the away call till it is over or a camp's own stop;
  /// the dawn's work each day at the ground.
  void camp(Ground ground, {required bool trapping}) {
    final at = HuntAt.ground(ground);
    for (var i = 0; i < 80 && g.me.hunt.trip != null; i++) {
      final t = g.me.hunt.trip!;
      if (trapping && t.there(g.today, HuntSun.dawn(g.today) + 30)) {
        for (final w in TrapWindow.values) {
          final m = switch (w) {
            TrapWindow.dawn => HuntSun.dawn(g.today) + 30,
            TrapWindow.midday => 720,
            TrapWindow.evening => HuntSun.sunset(g.today) - 30,
          };
          send(SpotFalcon(me, at, minute: m));
          for (final l in [Lure.pigeon, Lure.birdNet, Lure.pigeon]) {
            send(ReleaseLure(me, at, l, minute: m));
          }
        }
        // the first bird kept, the second entered, the third left to the
        // close
        final h = g.me.hunt;
        for (final f in [...h.held]) {
          if (h.falcons.where((x) => x.keep).isEmpty) {
            send(KeepBird(me, f.id));
          } else if (!seen.contains('fate:entered')) {
            send(EnterTrapAuction(me, f.id));
          }
        }
        send(CareFalcons(me)); // (from the camp: refused)
      }
      if (!trapping && t.there(g.today, HuntSun.sunrise(g.today) + 60)) {
        for (final f in [...g.me.hunt.falcons]) {
          for (var k = 0; k < 4; k++) {
            send(
              CastFalcon(
                me,
                f.id,
                at,
                minute: HuntSun.sunrise(g.today) + 90 + 90 * k,
              ),
            );
            if (f.where == FalconWhere.lost) {
              send(SearchFalcon(me, f.id));
              send(SearchFalcon(me, f.id)); // (twice a day: refused)
            }
          }
        }
      }
      final l = Trips.leg(g);
      if (l == null) {
        days(1);
        continue;
      }
      final plan = AwayPlan(
        l.plan.target,
        extra: l.plan.extra,
        counters: [...l.plan.counters, (game, events, summary) => note(events)],
        card: l.plan.card,
      );
      final run = AwayRun(g, plan);
      while (!run.done) {
        run.step();
      }
      final stop = run.stop!;
      seen.add(
        'stop:${stop.kind.name}${stop.extra == null ? '' : ':${stop.extra}'}',
      );
      for (final k in stop.also) {
        seen.add('stop:${k.name}');
      }
      if (stop.kind == AwayStopKind.extra) send(EndTrip(me));
    }
  }

  // refusals before anything is had
  send(StartTrip(me, TripKind.trapping, Ground.lith, 5)); // (out of season)
  send(BuyPermit(me, PermitKind.hunting)); // (no falcon with a passport)
  send(CareFalcons(me)); // (no falcons)
  send(BuildFacility(me, Facility.falconRoom));
  send(BuyPermit(me, PermitKind.trapping));
  send(BuyPermit(me, PermitKind.trapping)); // (held)
  for (final (x, n) in [
    (Gear.pigeon, 20),
    (Gear.pigeonNet, 1),
    (Gear.birdNet, 1),
    (Gear.binoculars, 1),
    (Gear.mobileTent, 1),
    (Gear.supplies, 30),
  ]) {
    send(OrderGear(me, x, n));
  }
  send(OrderGear(me, Gear.binoculars, 1)); // (enough)
  send(BuyFalcon(me, 'breeders:${g.today.value}:0', 100000)); // (closed)
  g.advanceTo(GameDay.ofDate(DateTime.utc(2026, 10)));
  yield line('ready');
  // a falcon from the exhibition, with its tracker
  for (var i = 0; i < 6 && g.me.hunt.falcons.isEmpty; i++) {
    final lots = FalconMarket.lots(
      g.state.world.seed,
      FalconRoute.exhibition,
      g.today,
    );
    if (lots.isNotEmpty) send(BuyFalcon(me, lots.first.key, 1000000));
    if (g.me.hunt.falcons.isEmpty) days(1);
  }
  send(BuyFalcon(me, 'trapping:${g.today.value}:9', 100000)); // (no lot)
  final bought = g.me.hunt.falcons.first;
  send(OrderGear(me, Gear.tracker, 1, falcon: bought.id));
  send(OrderGear(me, Gear.tracker, 1, falcon: bought.id)); // (on its way)
  send(ReleaseFalcon(me, bought.id)); // (not his to free: bought)
  send(EnterTrapAuction(me, bought.id)); // (not a held bird)
  send(SearchFalcon(me, bought.id)); // (not lost)
  send(
    CastFalcon(me, bought.id, const HuntAt.off(HuntOff.farm), minute: 600),
  ); // (by the farm)
  send(StartTrip(me, TripKind.trapping, Ground.estate, 3)); // (off ground)
  send(StartTrip(me, TripKind.trapping, Ground.lith, 0)); // (too far)
  // three days' الدعو for it, so that left at the farm it would step back
  for (var i = 0; i < 3; i++) {
    send(CareFalcons(me));
    days(1);
  }
  send(OrderGear(me, Gear.tracker, 1, falcon: bought.id)); // (it has one)
  send(
    SpotFalcon(
      me,
      const HuntAt.ground(Ground.lith),
      minute: HuntSun.dawn(g.today) + 30,
    ),
  ); // (no trip at all)
  yield line('bought');
  // the first camp: the coast, 50 nights on 30 days' supplies (the supplies
  // run out); the falcon at the farm uncared stops a night on the way
  send(StartTrip(me, TripKind.trapping, Ground.lith, 50));
  send(StartTrip(me, TripKind.trapping, Ground.lith, 5)); // (on a trip)
  send(
    SpotFalcon(
      me,
      const HuntAt.ground(Ground.lith),
      minute: HuntSun.dawn(g.today) + 30,
    ),
  ); // (still on the road)
  send(SpotFalcon(me, const HuntAt.ground(Ground.lith), minute: 60)); // night
  send(
    SpotFalcon(
      me,
      const HuntAt.ground(Ground.nafudEdge),
      minute: HuntSun.dawn(g.today) + 30,
    ),
  ); // (a hunting ground: off the trapping grounds)
  camp(Ground.lith, trapping: true);
  while (g.me.hunt.trip != null) {
    days(1);
  }
  yield line('home');
  // the second camp, to the season's end at القنفذة
  send(OrderGear(me, Gear.supplies, 40));
  days(1);
  send(StartTrip(me, TripKind.trapping, Ground.qunfudhah, 60));
  camp(Ground.qunfudhah, trapping: true);
  while (g.me.hunt.trip != null) {
    days(1);
  }
  // the auction's close: a bird neither sold nor kept is set free
  if (g.today < GameDay.ofDate(DateTime.utc(2026, 12, 2))) {
    note(g.advanceTo(GameDay.ofDate(DateTime.utc(2026, 12, 2))));
  }
  if (g.me.ledger.any((e) => e.category == LedgerCategory.falconSale)) {
    seen.add('fate:sold');
  }
  send(StartTrip(me, TripKind.trapping, Ground.lith, 5)); // (out of season)
  yield line('season');
  // الدعو for four weeks, then the hunting permit and a trip at the estate
  for (var i = 0; i < HuntBalance.dauDaysNeeded + 1; i++) {
    send(CareFalcons(me));
    days(1);
  }
  send(BuyPermit(me, PermitKind.hunting));
  send(StartTrip(me, TripKind.falconry, Ground.estate, 30));
  send(
    CastFalcon(
      me,
      bought.id,
      const HuntAt.ground(Ground.estate),
      inCar: true,
      moving: true,
      minute: HuntSun.sunrise(g.today) + 90,
    ),
  ); // (from a moving car)
  send(
    CastFalcon(
      me,
      bought.id,
      const HuntAt.ground(Ground.estate),
      minute: HuntSun.sunrise(g.today) + 30,
    ),
  ); // (before the hunting hour)
  camp(Ground.estate, trapping: false);
  while (g.me.hunt.trip != null) {
    days(1);
  }
  yield line('falconry');
  // the winter: a kept peregrine set free in February, not before
  final kept = g.me.hunt.falcons.where((f) => f.keep).toList();
  for (final f in kept) {
    send(ReleaseFalcon(me, f.id)); // (January: refused)
    send(EnterTrapAuction(me, f.id)); // (kept: not for sale)
  }
  note(g.advanceTo(GameDay.ofDate(DateTime.utc(2027, 2, 2))));
  for (final f in kept) {
    send(ReleaseFalcon(me, f.id));
  }
  note(g.advanceTo(GameDay.ofDate(DateTime.utc(2027, 6, 2))));
  send(CareFalcons(me)); // (the moult)
  yield line('spring');
  // a second autumn on the north coast's sister, all season: what the first
  // did not net it may (a bird left at the close, those released)
  note(g.advanceTo(GameDay.ofDate(DateTime.utc(2027, 9, 25))));
  send(BuyPermit(me, PermitKind.trapping));
  send(OrderGear(me, Gear.supplies, 60));
  send(OrderGear(me, Gear.pigeon, gearRoom(g.me, Gear.pigeon)));
  note(g.advanceTo(GameDay.ofDate(DateTime.utc(2027, 10))));
  send(StartTrip(me, TripKind.trapping, Ground.wajh, 60));
  camp(Ground.wajh, trapping: true);
  while (g.me.hunt.trip != null) {
    days(1);
  }
  note(g.advanceTo(GameDay.ofDate(DateTime.utc(2027, 12, 2))));
  yield line('second autumn');
}

/// The seed whose hunting run covers every path (chosen by
/// tool/hunt_seed.dart; the test checks it still does).
const huntSeed = 261;

/// The paths the hunting run must cover (huntLines' [covered]).
const huntPaths = {
  'trap:netted',
  'trap:released',
  'trap:stooped',
  'trap:nothingCame',
  'released:saker',
  'released:resident',
  'fate:kept',
  'fate:entered',
  'fate:sold',
  'fate:freedAtClose',
  'fate:freed',
  'fate:cared',
  'searched',
  'cast:lost',
  'cast:caught',
  'cast:missed',
  'stop:extra:suppliesOut',
  'stop:extra:seasonEnd',
  'stop:falconCare',
  'refused:outOfSeason',
  'refused:needsFalcon',
  'refused:noFalcons',
  'refused:permitHeld',
  'refused:gearFull',
  'refused:routeClosed',
  'refused:notALot',
  'refused:hasTracker',
  'refused:trackerComing',
  'refused:noTrip',
  'refused:notKept',
  'refused:notHeld',
  'refused:notLost',
  'refused:nearFarm',
  'refused:offGround',
  'refused:tooFar',
  'refused:onTrip',
  'refused:driving',
  'refused:night',
  'refused:awayFromFarm',
  'refused:movingCar',
  'refused:notByDay',
  'refused:releaseMonths',
  'refused:keptNotForSale',
  'refused:moult',
  'refused:searchedToday',
};
