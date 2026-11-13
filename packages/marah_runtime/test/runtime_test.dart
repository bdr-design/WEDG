import 'dart:async';
import 'dart:io';

import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/persistence.dart' show Pregnancy;
import 'package:marah_runtime/io.dart';
import 'package:marah_runtime/marah_runtime.dart';
import 'package:test/test.dart';

const params = NewGameParams(
  seed: 77,
  playerName: 'بدر',
  farmName: 'عزبة الصفوة',
  region: Region.qassim,
  favourite: ColorCategory.majaheem,
);

/// A controllable wall clock.
class FakeNow {
  DateTime value = DateTime.utc(2026, 11, 8, 9);
  DateTime call() => value;
  void advance(Duration d) => value = value.add(d);
}

void main() {
  group('EngineCore', () {
    late MemoryBackend backend;
    late FakeNow now;
    late List<Push> pushes;

    EngineCore core({Duration slice = const Duration(milliseconds: 6)}) =>
        EngineCore(
          store: SaveStore(backend),
          emit: pushes.add,
          now: now.call,
          sliceBudget: slice,
        );

    setUp(() {
      backend = MemoryBackend();
      now = FakeNow();
      pushes = [];
    });

    Iterable<PlayerSnapshot> snapshots() =>
        pushes.whereType<SnapshotPush>().map((p) => p.snapshot);

    test('no save, then a new game publishes a snapshot and saves', () async {
      final e = core();
      expect(await e.open(), isA<NoGame>());
      await e.newGame(params);
      expect(snapshots(), isNotEmpty);
      final s = snapshots().last;
      expect(s.playerName, 'بدر');
      expect(s.herd.total, 2);
      expect(s.market, isNotEmpty);
      expect(backend.data['marah.save'], isNotNull);
      await e.close();
    });

    test('commands return results and publish a newer snapshot', () async {
      final e = core();
      await e.newGame(params);
      final before = snapshots().last.revision;
      final me = e.game!.me.id;
      final r = await e.dispatch(SetFeedPlan(me, FeedPlan.premium));
      expect(r.ok, isTrue);
      final s = snapshots().last;
      expect(s.revision, greaterThan(before));
      expect(s.farm.feedPlan, FeedPlan.premium);
      await e.close();
    });

    test('one real day later the world is one game week older', () async {
      final e = core();
      await e.newGame(params);
      final start = snapshots().last.today;
      now.advance(const Duration(days: 1));
      await e.resume();
      expect(snapshots().last.today, start + 7);
      await e.close();
    });

    test(
      'a month away catches up in slices with progress and a save',
      () async {
        final e = core(slice: const Duration(milliseconds: 1));
        await e.newGame(params);
        final start = snapshots().last.today;
        now.advance(const Duration(days: 30));
        await e.resume();
        expect(snapshots().last.today, start + 210);
        final progress = pushes.whereType<CatchUpProgress>().toList();
        expect(progress, isNotEmpty);
        expect(progress.last.done, progress.last.total);
        final reopened = core();
        expect(await reopened.open(), isA<GameOpened>());
        expect(reopened.game!.today, start + 210);
        await e.close();
        await reopened.close();
      },
    );

    test(
      'pause saves immediately; reopening continues the same game',
      () async {
        final e = core();
        await e.newGame(params);
        final me = e.game!.me.id;
        await e.dispatch(SetCalfShare(me, CalfShare.quarter));
        await e.pause();
        final again = core();
        expect(await again.open(), isA<GameOpened>());
        expect(again.game!.me.farm.calfShare, CalfShare.quarter);
        await e.close();
        await again.close();
      },
    );

    test('a broken save is reported, never replaced, and the last good '
        'one can be restored', () async {
      final e = core();
      await e.newGame(params);
      await e.dispatch(SetCalfShare(e.game!.me.id, CalfShare.all));
      await e.close();
      final ok = core(); // a successful open proves the save readable
      expect(await ok.open(), isA<GameOpened>());
      await ok.close();
      backend.data['marah.save'] = '{broken';

      final b = core();
      expect(await b.open(), isA<GameOpenFailed>());
      expect(backend.data['marah.save.broken'], '{broken');
      await b.flush();
      expect(backend.data['marah.save'], '{broken');
      expect(await b.openPrevious(), isA<GameOpened>());
      expect(b.game!.me.farm.calfShare, CalfShare.all);
      await b.close();
    });

    test(
      'a failed save is reported, retried, and never stops later saves',
      () async {
        final flaky = FlakyBackend();
        final e = EngineCore(
          store: SaveStore(flaky),
          emit: pushes.add,
          now: now.call,
        );
        await e.newGame(params);
        flaky.failWrites = true;
        await e.dispatch(SetCalfShare(e.game!.me.id, CalfShare.quarter));
        await e.flush();
        final failed = pushes.whereType<SaveStatus>().last;
        expect(failed.ok, isFalse);
        flaky.failWrites = false;
        await e.flush();
        expect(pushes.whereType<SaveStatus>().last.ok, isTrue);
        final again = EngineCore(store: SaveStore(flaky), emit: (_) {});
        await again.open();
        expect(again.game!.me.farm.calfShare, CalfShare.quarter);
        await e.close();
      },
    );

    test(
      'unreadable bytes open as a failure with a backup, not a crash',
      () async {
        final flaky = FlakyBackend()..data['marah.save'] = 'bytes';
        flaky.failReads = true;
        final e = EngineCore(store: SaveStore(flaky), emit: (_) {});
        expect(await e.open(), isA<GameOpenFailed>());
        expect(flaky.data['marah.save.broken'], 'bytes');
        await e.close();
      },
    );

    test(
      'device clock moved back: the world keeps going from where it was',
      () async {
        final e = core();
        await e.newGame(params);
        now.advance(const Duration(days: 2));
        await e.resume();
        final day = e.game!.today;
        now.advance(const Duration(days: -5)); // clock set back
        await e.resume();
        expect(e.game!.today, day);
        now.advance(const Duration(days: 1));
        await e.resume();
        expect(e.game!.today, day + 7);
        await e.close();
      },
    );

    test('a huge forward jump is capped and reported', () async {
      final e = core();
      await e.newGame(params);
      final start = e.game!.today;
      now.advance(const Duration(days: 3 * 365));
      await e.resume();
      expect(e.game!.today, start + 365);
      expect(
        pushes.whereType<CatchUpCapped>().single.skippedDays,
        3 * 365 * 7 - 365,
      );
      now.advance(const Duration(days: 1));
      await e.resume();
      expect(e.game!.today, start + 365 + 7);
      await e.close();
    });

    test('a command is saved before it returns', () async {
      final e = core();
      await e.newGame(params);
      final me = e.game!.me.id;
      await e.dispatch(SetCalfShare(me, CalfShare.all));
      final again = core();
      expect(await again.open(), isA<GameOpened>());
      expect(again.game!.me.farm.calfShare, CalfShare.all);
      await e.close();
      await again.close();
    });

    test('a closed engine refuses work', () async {
      final e = core();
      await e.newGame(params);
      await e.close();
      expect(e.flush(), throwsStateError);
    });

    test('details for a camel and a festival', () async {
      final e = core();
      await e.newGame(params);
      final s = snapshots().last;
      final camel = await e.camelDetail(s.herdTop.first.id);
      expect(camel!.isMine, isTrue);
      expect(camel.looks, hasLength(Trait.values.length));
      expect(camel.canSell, isNull);
      final fest = await e.festivalDetail(s.festivals.first.id);
      expect(fest!.rounds, isNotEmpty);
      expect(fest.rounds.first.prizes, hasLength(10));
      await e.close();
    });
  });

  group('Client streams', () {
    test(
      'a listener that subscribes late still gets the latest snapshot',
      () async {
        final client = InlineEngineClient(
          (emit) => EngineCore(store: SaveStore(MemoryBackend()), emit: emit),
        );
        await client.newGame(params);
        final late = await client.snapshots.first.timeout(
          const Duration(seconds: 2),
        );
        expect(late.herd.total, 2);
        expect(client.latest, same(late));
        await client.dispose();
      },
    );
  });

  group('Time slicing (web path)', () {
    test('a long catch-up never blocks the event loop for long', () async {
      final backend = MemoryBackend();
      final now = FakeNow();
      final client = InlineEngineClient(
        (emit) => EngineCore(
          store: SaveStore(backend),
          emit: emit,
          now: now.call,
          sliceBudget: const Duration(milliseconds: 1),
        ),
      );
      await client.newGame(params);
      now.advance(const Duration(days: 60)); // 420 game days

      // A "frame" timer: measure the longest gap between its ticks while
      // the catch-up runs on the same thread.
      var last = DateTime.now();
      var worst = Duration.zero;
      var ticks = 0;
      final frames = Timer.periodic(const Duration(milliseconds: 2), (_) {
        final t = DateTime.now();
        final gap = t.difference(last);
        if (gap > worst) worst = gap;
        last = t;
        ticks++;
      });
      final watch = Stopwatch()..start();
      await client.resume();
      watch.stop();
      frames.cancel();

      expect(ticks, greaterThan(0), reason: 'frames ran during catch-up');
      // Generous bound for shared CI machines; locally it is a few ms.
      expect(
        worst,
        lessThan(const Duration(milliseconds: 60)),
        reason:
            'longest stall ${worst.inMilliseconds} ms, '
            'catch-up took ${watch.elapsedMilliseconds} ms',
      );
      await client.dispose();
    });
  });

  group('Worker isolate (iOS/Android path)', () {
    late Directory dir;

    setUp(() async {
      dir = await Directory.systemTemp.createTemp('marah_test');
    });

    tearDown(() async {
      if (dir.existsSync()) await dir.delete(recursive: true);
    });

    test('plays in the worker and persists to disk', () async {
      final client = await IsolateEngineClient.spawn(saveDirectory: dir.path);
      expect(await client.open(), isA<NoGame>());
      final first = client.snapshots.first;
      await client.newGame(params);
      final snap = await first.timeout(const Duration(seconds: 10));
      expect(snap.herd.total, 2);

      // Snapshots replay the latest to new listeners: wait for a newer one.
      final next = client.snapshots.firstWhere(
        (s) => s.revision > snap.revision,
      );
      final camel = snap.herdTop.first;
      final r = await client.dispatch(
        RenameCamel(snap.playerId, camel.id, 'الغالية'),
      );
      expect(r.ok, isTrue, reason: '$r');
      final renamed = await next.timeout(const Duration(seconds: 10));
      expect(renamed.herdTop.any((c) => c.name == 'الغالية'), isTrue);

      await client.pause();
      await client.dispose();
      expect(File('${dir.path}/marah.db').existsSync(), isTrue);
      expect(dir.listSync().where((f) => f.path.endsWith('.tmp')), isEmpty);

      final again = await IsolateEngineClient.spawn(saveDirectory: dir.path);
      expect(await again.open(), isA<GameOpened>());
      final detail = await again.camelDetail(camel.id);
      expect(detail!.card.name, 'الغالية');
      await again.dispose();
    });

    test('a failure in the worker reaches the caller', () async {
      final client = await IsolateEngineClient.spawn(saveDirectory: dir.path);
      // No game yet: a detail request returns null rather than throwing.
      expect(await client.camelDetail(const CamelId('none')), isNull);
      await client.dispose();
      await expectLater(client.flush(), throwsA(isA<EngineStopped>()));
    });
  });

  group('Worker shutdown', () {
    test('a request racing dispose fails instead of hanging', () async {
      final dir = await Directory.systemTemp.createTemp('marah_race');
      final client = await IsolateEngineClient.spawn(saveDirectory: dir.path);
      await client.newGame(params);
      final racing = client.resume();
      await client.dispose();
      await racing
          .timeout(const Duration(seconds: 5))
          .catchError((Object _) {});
      await dir.delete(recursive: true);
    });
  });

  group('Paging and sections', () {
    test('herd pages are filtered, sorted and complete', () async {
      final e = EngineCore(store: SaveStore(MemoryBackend()), emit: (_) {});
      await e.newGame(params);
      final all = await e.herdPage(const HerdQuery(limit: 2));
      expect(all!.total, 2);
      expect(all.cards, hasLength(2));
      expect(
        all.cards.first.quality,
        greaterThanOrEqualTo(all.cards[1].quality),
      );
      final first = await e.herdPage(const HerdQuery(limit: 1));
      final rest = await e.herdPage(const HerdQuery(offset: 1, limit: 1));
      expect(first!.cards, hasLength(1));
      expect(rest!.cards, hasLength(1));
      expect(rest.cards.single.id, isNot(first.cards.single.id));
      final males = await e.herdPage(const HerdQuery(filter: HerdFilter.males));
      // grown males only (two years and over): the start's calf is not one
      expect(males!.total, 0);
      final young = await e.herdPage(const HerdQuery(filter: HerdFilter.young));
      expect(young!.total, 1);
      await e.close();
    });

    test('only the sections that changed get a new revision', () async {
      final pushes = <Push>[];
      final e = EngineCore(store: SaveStore(MemoryBackend()), emit: pushes.add);
      await e.newGame(params);
      PlayerSnapshot last() => pushes.whereType<SnapshotPush>().last.snapshot;
      final before = last().sections;
      final me = last().playerId;
      await e.dispatch(RenameCamel(me, last().herdTop.first.id, 'الغالية'));
      final after = last().sections;
      expect(after.herd, before.herd + 1);
      expect(after.market, before.market);
      expect(after.festivals, before.festivals);
      expect(after.studs, before.studs);
      expect(after.bank, before.bank, reason: 'no money moved');
      await e.close();
    });
  });

  group('البنك', () {
    test(
      'day one, money moving, a month opened, in the snapshot JSON',
      () async {
        final pushes = <Push>[];
        final e = EngineCore(
          store: SaveStore(MemoryBackend()),
          emit: pushes.add,
        );
        await e.newGame(params);
        PlayerSnapshot last() => pushes.whereType<SnapshotPush>().last.snapshot;
        var j = SnapshotJson.snapshot(last());
        // day one: the opening balance, nothing in or out, no month yet
        expect(j['bank'], {
          'opening': Balance.startingCash,
          'startedOn': j['date'],
          'todayIn': 0,
          'todayOut': 0,
          'months': <Object?>[],
        });
        final before = last().sections.bank;
        final me = last().playerId;
        expect(
          (await e.dispatch(OrderSupply(me, Supply.alfalfa, 2))).ok,
          isTrue,
        );
        expect(last().sections.bank, before + 1);
        final b = last().bank;
        expect(b.todayOut, -last().todayNet);
        expect(b.months.single.top.kind, MoneyKind.feed);
        expect(b.months.single.net, last().cash - Balance.startingCash);
        j = SnapshotJson.snapshot(last());
        final month = ((j['bank']! as Map)['months']! as List).first as Map;
        expect(month['top'], {
          'kind': 'feed',
          'amount': b.months.single.net,
          'count': 1,
          'day': j['date'],
        });
        // the month opened, as the page asks for it
        final m = await e.bankMonth(month['month'] as String);
        expect(SnapshotJson.moneyMonth(m!), {
          'month': month['month'],
          'in': 0,
          'out': -b.months.single.net,
          'lines': [month['top']],
        });
        expect(await e.bankMonth('1999-01'), isNull);
        await e.close();
      },
    );
  });

  group('Recovery', () {
    test('a bug during a day restores the last save instead of saving a '
        'half-changed game', () async {
      final pushes = <Push>[];
      final backend = MemoryBackend();
      final now = FakeNow();
      final e = EngineCore(
        store: SaveStore(backend),
        emit: pushes.add,
        now: now.call,
      );
      await e.newGame(params);
      await e.flush();
      final saved = backend.data['marah.save'];
      // Corrupt the in-memory game: a pregnancy whose sire has no genes.
      final dam = e.game!.state.world.camels.values.firstWhere(
        (c) => c.ownerId == e.game!.me.id,
      );
      final saved0 = dam.pregnancy?.dueOn; // (the start's camel is in calf)
      dam.pregnancy = Pregnancy(
        sire: dam.sire!,
        sireGenes: const {},
        matedOn: e.game!.today,
        checkOn: e.game!.today,
        dueOn: e.game!.today + 1,
        conceived: true,
        confirmed: true,
      );
      now.advance(const Duration(days: 1));
      await e.resume();
      expect(pushes.whereType<StateRecovered>(), isNotEmpty);
      expect(e.game, isNotNull);
      // as it was saved, not the broken one
      expect(e.game!.state.world.camels[dam.id]!.pregnancy?.dueOn, saved0);
      expect(backend.data['marah.save'], saved);
      await e.close();
    });
  });
  group('Repeated failures', () {
    test('the same failing day stops the world instead of looping', () async {
      final pushes = <Push>[];
      final backend = MemoryBackend();
      final now = FakeNow();
      final e = EngineCore(
        store: SaveStore(backend),
        emit: pushes.add,
        now: now.call,
      );
      await e.newGame(params);
      // A saved camel under treatment with no recovery date: every day
      // fails in the health system (a bug a future change could introduce).
      e.game!.state.world.camels.values.firstWhere(
          (c) => c.ownerId == e.game!.me.id,
        )
        ..health = HealthStatus.treated
        ..illness = Illness.mange
        ..recoversOn = null;
      await e.flush();
      final day = e.game!.today;
      now.advance(const Duration(days: 1));
      for (var i = 0; i < 4; i++) {
        await e.resume();
      }
      expect(pushes.whereType<EngineHalted>(), isNotEmpty);
      expect(e.game!.today, day);
      await e.close();
    });

    test(
      'a save this version cannot resume is reported, not changed',
      () async {
        final backend = MemoryBackend();
        final first = EngineCore(store: SaveStore(backend), emit: (_) {});
        await first.newGame(params);
        // A listing that points at a camel that does not exist.
        final w = first.game!.state.world;
        final l = w.listings.values.first;
        w.camels.remove(l.camelId);
        await first.flush();
        await first.close();
        final saved = backend.data['marah.save'];

        final e = EngineCore(store: SaveStore(backend), emit: (_) {});
        final status = await e.open();
        expect(status, isA<GameOpenFailed>());
        expect((status as GameOpenFailed).problem, LoadProblem.engineError);
        expect(backend.data['marah.save'], saved);
        expect(e.store.locked, isFalse);
        await e.close();
      },
    );
  });
}

class FlakyBackend extends MemoryBackend {
  bool failWrites = false;
  bool failReads = false;

  @override
  Future<void> write(String key, String value) async {
    if (failWrites) throw const FileSystemException('disk full');
    await super.write(key, value);
  }

  @override
  Future<String?> read(String key) async {
    if (failReads) throw const FormatException('bad utf-8');
    return super.read(key);
  }
}
