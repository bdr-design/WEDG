import 'dart:async';
import 'dart:io';

import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/marah_domain.dart';
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
          autosaveDelay: const Duration(milliseconds: 10),
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
      expect(s.herd, hasLength(3));
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
        await e.dispatch(SetShepherds(me, 4));
        await e.pause();
        final again = core();
        expect(await again.open(), isA<GameOpened>());
        expect(again.game!.me.farm.shepherds, 4);
        await e.close();
        await again.close();
      },
    );

    test('a broken save is reported, never replaced, and the previous one '
        'can be restored', () async {
      final e = core();
      await e.newGame(params);
      await e.dispatch(SetShepherds(e.game!.me.id, 2));
      await e.flush();
      await e.close();
      backend.data['marah.save'] = '{broken';

      final b = core();
      final status = await b.open();
      expect(status, isA<GameOpenFailed>());
      await b.dispatch(const SetShepherds(OwnerId('x'), 3));
      await b.flush();
      expect(backend.data['marah.save'], '{broken');
      expect(await b.openPrevious(), isA<GameOpened>());
      expect(b.game, isNotNull);
      await b.close();
    });

    test('details for a camel and a festival', () async {
      final e = core();
      await e.newGame(params);
      final s = snapshots().last;
      final camel = await e.camelDetail(s.herd.first.id);
      expect(camel!.isMine, isTrue);
      expect(camel.looks, hasLength(Trait.values.length));
      expect(camel.canSell, isNull);
      final fest = await e.festivalDetail(s.festivals.first.id);
      expect(fest!.rounds, isNotEmpty);
      expect(fest.rounds.first.prizes, hasLength(10));
      await e.close();
    });
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

      expect(ticks, greaterThan(3), reason: 'frames ran during catch-up');
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
      expect(snap.herd, hasLength(3));

      final next = client.snapshots.first;
      final camel = snap.herd.first;
      final r = await client.dispatch(
        RenameCamel(snap.playerId, camel.id, 'الغالية'),
      );
      expect(r.ok, isTrue, reason: '$r');
      final renamed = await next.timeout(const Duration(seconds: 10));
      expect(renamed.herd.any((c) => c.name == 'الغالية'), isTrue);

      await client.pause();
      await client.dispose();
      expect(File('${dir.path}/marah.save').existsSync(), isTrue);
      expect(File('${dir.path}/marah.save.tmp').existsSync(), isFalse);

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
      await expectLater(client.flush(), throwsStateError);
    });
  });

  group('FileBackend', () {
    test('writes atomically and leaves no temp file', () async {
      final dir = await Directory.systemTemp.createTemp('marah_fb');
      final fb = FileBackend(dir.path);
      await fb.write('k', 'one');
      await fb.write('k', 'two');
      expect(await fb.read('k'), 'two');
      expect(File('${dir.path}/k.tmp').existsSync(), isFalse);
      await fb.delete('k');
      expect(await fb.read('k'), isNull);
      await dir.delete(recursive: true);
    });
  });
}
