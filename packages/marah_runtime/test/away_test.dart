// The away call (task T15: docs/proposals/rush_and_calendar.md section 5):
// a jumped stretch equals the same days played by the clock; the landing;
// «وقّف هنا»; the save marked good after; the truck's hour from the clock.
import 'dart:convert';

import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_runtime/marah_runtime.dart';
import 'package:test/test.dart';

const params = NewGameParams(
  seed: 4242,
  playerName: 'p',
  farmName: 'f',
  region: Region.qassim,
  favourite: ColorCategory.wodh,
);

class FakeNow {
  DateTime value = DateTime.utc(2026, 11, 14, 9);
  DateTime call() => value;
}

/// The world and the players, without the clock's anchor (which a jump
/// moves on purpose): what must be equal however the days were run.
String worldOf(Game g) {
  final j = g.state.toJson();
  return jsonEncode({
    'world': j['world'],
    'players': j['players'],
    'inboxes': j['inboxes'],
  });
}

void main() {
  late FakeNow now;
  late List<Push> pushes;
  late MemoryBackend backend;

  EngineCore core({Future<void> Function()? yielder, Duration? slice}) =>
      EngineCore(
        store: SaveStore(backend),
        emit: pushes.add,
        now: now.call,
        yielder: yielder,
        sliceBudget: slice ?? const Duration(milliseconds: 6),
      );

  setUp(() {
    now = FakeNow();
    pushes = [];
    backend = MemoryBackend();
  });

  /// [e]'s clock moved on to [minute] of [day] and caught up: the days
  /// played as the clock brings them.
  Future<void> playTo(EngineCore e, GameDay day, int minute) async {
    final s = e.game!.state;
    final len = Duration.microsecondsPerDay ~/ 7;
    final anchor = DateTime.fromMillisecondsSinceEpoch(
      s.startedAtUtcMs + s.clockShiftMs,
      isUtc: true,
    );
    now.value = anchor.add(
      Duration(
        microseconds:
            day.daysSince(s.startedOn) * len + (minute * len + 1439) ~/ 1440,
      ),
    );
    await e.catchUp();
    expect(e.game!.today, day);
  }

  /// [e] jumped to [day] in as many legs as its stops make (the player
  /// going on after each), landing at 06:00.
  Future<List<AwayStopKind>> jumpTo(EngineCore e, GameDay day) async {
    final stops = <AwayStopKind>[];
    while (e.game!.today < day) {
      final r = await e.away(day);
      if (r.refused?.params['reason'] == 'round') {
        // his round's day: he watches it told to its end, then goes on
        await playTo(e, e.game!.today, 1100);
        continue;
      }
      expect(r.refused, isNull, reason: '${r.refused}');
      stops.add(r.run!.stop!.kind);
    }
    return stops;
  }

  /// The same scripted start for both: a tanker on its way, a pen being
  /// built, the dam entered in her round, the standing orders and the vet's
  /// contract on (so a played day and a jumped day run them alike).
  Future<EngineCore> scripted() async {
    final e = core();
    await e.newGame(params);
    final g = e.game!, me = g.me.id;
    await e.dispatch(OrderSupply(me, Supply.water, 1, tanker: Tanker.small));
    await e.dispatch(BuildFacility(me, Facility.pen));
    await e.dispatch(SetStandingOrder(me, StandingOrder.water, on: true));
    await e.dispatch(SetStandingOrder(me, StandingOrder.feed, on: true));
    await e.dispatch(SignVetContract(me));
    final v = GameView(g.state, me);
    final dam = v.herd.firstWhere((c) => c.sex == Sex.female);
    final f = v.festivals.firstWhere(
      (f) => !f.done && f.opensOn <= g.today && g.today <= f.closesOn,
    );
    final (round, _) = v.ownRound(f.id, dam.id);
    await e.dispatch(EnterRound(me, f.id, round!, [dam.id]));
    return e;
  }

  test(
    'a jumped stretch equals the same days played, through a year',
    () async {
      // 300 days: deliveries, a build, the round's day, a calving (the dam is
      // due at the end of March), the 1sts (the contract's fee), the season's
      // planning (2 July), the standing orders
      final a = await scripted();
      final day = a.game!.today + 300;
      await playTo(a, day, 360);
      final playedA = worldOf(a.game!);
      await a.close();

      backend = MemoryBackend();
      now = FakeNow();
      final b = await scripted();
      final stops = await jumpTo(b, day);
      expect(stops, contains(AwayStopKind.round));
      expect(stops.last, AwayStopKind.target);
      expect(worldOf(b.game!), playedA);
      expect(
        b.game!.state.world.camels.values.any(
          (c) => c.born > b.game!.state.startedOn,
        ),
        isTrue,
        reason: 'a calving in the stretch',
      );
      await b.close();
    },
  );

  test('a short day rushed, then ten days played or jumped: equal', () async {
    Future<EngineCore> toShort() async {
      final e = core();
      await e.newGame(params);
      final g = e.game!;
      while (!g.me.farm.short.contains(Supply.water)) {
        await playTo(e, g.today + 1, 360);
      }
      final me = g.me.id;
      final r = await e.dispatch(
        OrderSupply(me, Supply.water, 1, tanker: Tanker.small, now: true),
      );
      expect(r.ok, isTrue, reason: '$r');
      return e;
    }

    final a = await toShort();
    final day = a.game!.today + 10;
    await playTo(a, day, 360);
    final played = worldOf(a.game!);
    await a.close();
    backend = MemoryBackend();
    now = FakeNow();
    final b = await toShort();
    await jumpTo(b, day);
    expect(worldOf(b.game!), played);
    await b.close();
  });

  test(
    'the landing: 06:00 of the day reached, the next catch-up runs nothing',
    () async {
      final e = core();
      await e.newGame(params);
      final g = e.game!;
      final target = g.today + 20;
      final r = await e.away(target);
      final landed = g.today;
      expect(r.run!.stop, isNotNull);
      expect(e.minuteOfDay(), 360);
      expect(g.state.clock(now: now.call).today(), landed);
      await e.catchUp();
      expect(g.today, landed);
      expect(pushes.whereType<AwayProgress>(), isNotEmpty);
      await e.close();
    },
  );

  test(
    'his round: landed at 06:00 before any stage, then six tellings',
    () async {
      final e = await scripted();
      final g = e.game!;
      final r = await e.away(g.today + 60);
      // the registration stop may come first; go on to the round
      var run = r.run!;
      while (run.stop!.kind != AwayStopKind.round) {
        run = (await e.away(g.today + 60)).run!;
      }
      final round = [
        for (final f in g.state.world.festivals.values)
          for (final x in f.rounds)
            if (x.day == g.today && x.entries.any((y) => y.ownerId == g.me.id))
              x,
      ].single;
      expect(round.judged, isTrue);
      expect(round.told, 0);
      expect(e.minuteOfDay(), 360);
      for (var i = 0; i < Balance.stageMinutes.length; i++) {
        await playTo(e, g.today, Balance.stageMinutes[i]);
        expect(round.told, i + 1);
      }
      // not left while the round is told; free once it is over
      expect(AwayRun.refusal(g, g.today + 5), isNull);
      await e.close();
    },
  );

  test('«وقّف هنا»: ends within a day of the stop flag', () async {
    late EngineCore e;
    var yields = 0;
    e = core(
      slice: Duration.zero,
      yielder: () async {
        if (++yields == 3) e.stopAway();
      },
    );
    await e.newGame(params);
    final g = e.game!;
    // stores filled so no store stops it first
    g.me.farm
      ..storeKg = 1 << 20
      ..tankL = 1 << 20
      ..barleyKg = 1e5
      ..alfalfaKg = 1e5
      ..waterL = 1e6;
    final start = g.today;
    final r = await e.away(start + 300);
    expect(
      r.run!.stop!.kind,
      isIn([AwayStopKind.cancelled, AwayStopKind.registration]),
    );
    expect(g.today.daysSince(start), lessThanOrEqualTo(4));
    await e.close();
  });

  test(
    'the save is marked good after: the save before cannot be opened',
    () async {
      final e = core();
      await e.newGame(params);
      final g = e.game!;
      final before = g.today;
      await e.away(before + 20);
      final landed = e.game!.today;
      expect(landed, greaterThan(before));
      expect(await e.openPrevious(), isA<GameOpened>());
      expect(e.game!.today, landed);
      await e.close();
    },
  );

  test(
    'refused: not ahead, more than a year, a sick camel without the vet',
    () async {
      final e = core();
      await e.newGame(params);
      final g = e.game!;
      expect((await e.away(g.today)).refused!.params['reason'], 'notAhead');
      expect((await e.away(g.today + 366)).refused!.params['reason'], 'tooFar');
      g.state.world.aliveOwnedBy(g.me.id).first
        ..health = HealthStatus.sick
        ..illness = Illness.mange
        ..sickSince = g.today;
      expect((await e.away(g.today + 5)).refused!.params['reason'], 'sick');
      await e.dispatch(SignVetContract(g.me.id));
      expect((await e.away(g.today + 5)).refused, isNull);
      await e.close();
    },
  );

  test('the truck\'s hour is the engine\'s: a stale one refused', () async {
    final e = core();
    await e.newGame(params);
    final g = e.game!, me = g.me.id;
    final l = GameView(g.state, me).market.toList()
      ..sort((a, b) => a.askPrice.value - b.askPrice.value);
    await e.dispatch(BuyListing(me, l.first.id));
    final hour = e.minuteOfDay() ~/ 60;
    final stale = await e.dispatch(
      RushTruck(me, l.first.camel.id, hour: (hour + 5) % 24),
    );
    expect((stale as Err).error.code, ErrorCode.priceChanged);
    final ok = await e.dispatch(RushTruck(me, l.first.camel.id));
    expect(ok.ok, isTrue);
    final c = g.state.world.camels[l.first.camel.id]!;
    expect(c.arrivedOn, g.today);
    expect(c.acquiredOn, g.today);
    await e.close();
  });
}
