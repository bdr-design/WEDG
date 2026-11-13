import 'dart:convert';
import 'dart:io';

import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:marah_domain/src/world_gen.dart';
import 'package:marah_domain/testing.dart';
import 'package:marah_store/marah_store.dart';
import 'package:sqlite3/sqlite3.dart';
import 'package:test/test.dart';

Game newGame([int seed = 7]) => Game.create(
  seed: seed,
  playerName: 'بدر',
  farmName: 'عزبة',
  region: Region.qassim,
  favourite: ColorCategory.majaheem,
  startedAt: DateTime.utc(2026, 11, 8),
);

String snap(GameState s) => jsonEncode(s.toJson());

void main() {
  late Directory dir;
  late String path;

  setUp(() async {
    dir = await Directory.systemTemp.createTemp('marah_store');
    path = '${dir.path}/marah.db';
  });

  tearDown(() async {
    if (dir.existsSync()) await dir.delete(recursive: true);
  });

  Future<GameState> reopen() async {
    final store = SqliteGameStore(path);
    final r = await store.open();
    await store.close();
    return (r as Opened).state;
  }

  test('no file means no save', () async {
    expect(await SqliteGameStore(path).open(), isA<NoSave>());
  });

  test('a saved game reads back exactly', () async {
    final g = newGame();
    final bot = Bot(g);
    for (var i = 0; i < 30; i++) {
      bot.week();
    }
    final store = SqliteGameStore(path);
    await store.startOver();
    await store.save(g.state);
    await store.close();
    expect(snap(await reopen()), snap(g.state));
  });

  test('saves only what changed', () async {
    final g = newGame();
    final store = SqliteGameStore(path);
    await store.startOver();
    await store.save(g.state);
    final first = store.lastWrite;
    expect(first.camels, g.state.world.camels.length);

    final c = GameView(g.state, g.me.id).herd.first;
    g.dispatch(RenameCamel(g.me.id, c.id, 'الغالية'));
    await store.save(g.state);
    expect(store.lastWrite.camels, 1);
    expect(store.lastWrite.docs, lessThanOrEqualTo(2)); // inbox only

    await store.save(g.state);
    expect(store.lastWrite, (camels: 0, docs: 0));
    await store.close();
    expect(snap(await reopen()), snap(g.state));
  });

  test('saving and reopening mid-game never changes what happens', () async {
    final straight = newGame(3);
    final botA = Bot(straight);
    var game = newGame(3);
    var store = SqliteGameStore(path);
    await store.startOver();
    for (var week = 0; week < 80; week++) {
      botA.week();
      Bot(game).week();
      await store.save(game.state);
      if (week % 7 == 0) {
        await store.close();
        store = SqliteGameStore(path);
        game = Game(((await store.open()) as Opened).state);
      }
    }
    await store.close();
    expect(snap(game.state), snap(straight.state));
  });

  List<String> backups(String prefix) {
    final d = Directory('${dir.path}/backups');
    if (!d.existsSync()) return [];
    return [
      for (final f in d.listSync())
        if (f.uri.pathSegments.last.startsWith(prefix) &&
            f.path.endsWith('.db'))
          f.path,
    ];
  }

  test('a garbage file is backed up, locked and never replaced', () async {
    File(path).writeAsStringSync('this is not a database');
    final store = SqliteGameStore(path);
    expect(await store.open(), isA<OpenFailed>());
    expect(store.locked, isTrue);
    expect(backups('broken'), hasLength(1));
    expect(
      File(backups('broken').single).readAsStringSync(),
      'this is not a database',
    );
    await store.save(newGame().state);
    expect(File(path).readAsStringSync(), 'this is not a database');
    // A second failed open keeps both copies.
    expect(await SqliteGameStore(path).open(), isA<OpenFailed>());
    expect(backups('broken'), hasLength(2));
  });

  Future<GameState> saveAndProve(Game g) async {
    final store = SqliteGameStore(path);
    await store.startOver();
    await store.save(g.state);
    expect(await store.markGood(), isTrue);
    await store.close();
    return g.state;
  }

  test(
    'the fallback is only refreshed when the engine proves a save good',
    () async {
      final g = newGame();
      await saveAndProve(g);
      expect(File('${dir.path}/backups/prev.db').existsSync(), isTrue);
      final opened = SqliteGameStore(path);
      expect(await opened.open(), isA<Opened>()); // open alone does not rotate
      await opened.close();
      expect(File('${dir.path}/backups/prev2.db').existsSync(), isFalse);
    },
  );

  test('restore keeps the current save and uses the last good one', () async {
    final g = newGame();
    await saveAndProve(g);
    File(path).writeAsStringSync('broken');
    for (final s in ['-wal', '-shm']) {
      final f = File('$path$s');
      if (f.existsSync()) f.deleteSync();
    }
    final b = SqliteGameStore(path);
    expect(await b.open(), isA<OpenFailed>());
    final restored = await b.openPrevious();
    expect(restored, isA<Opened>());
    expect(snap((restored as Opened).state), snap(g.state));
    expect(b.locked, isFalse);
    await b.close();
  });

  test('a damaged fallback is never used and the live save is kept', () async {
    final g = newGame();
    await saveAndProve(g);
    File('${dir.path}/backups/prev.db').writeAsStringSync('damaged');
    final store = SqliteGameStore(path);
    expect(await store.open(), isA<Opened>());
    expect(await store.openPrevious(), isA<NoSave>());
    await store.close();
    expect(snap(await reopen()), snap(g.state));
  });

  test(
    'a failed backup leaves the game playable and the old fallback',
    () async {
      final g = newGame();
      await saveAndProve(g);
      final prev = File('${dir.path}/backups/prev.db').readAsBytesSync();
      // Make the temp backup path unusable.
      Directory('${dir.path}/backups/prev.db.tmp').createSync();
      final store = SqliteGameStore(path);
      expect(await store.open(), isA<Opened>());
      expect(await store.markGood(), isFalse);
      expect(File('${dir.path}/backups/prev.db').readAsBytesSync(), prev);
      g.advanceDays(3);
      await store.save(g.state);
      await store.close();
      expect(snap(await reopen()), snap(g.state));
    },
  );

  test('starting over keeps a copy of the replaced save', () async {
    await saveAndProve(newGame());
    final store = SqliteGameStore(path);
    await store.open();
    await store.startOver();
    expect(backups('replaced'), hasLength(1));
    await store.save(newGame(5).state);
    await store.close();
  });

  test(
    'an upgrade keeps the original, applies the step and rebuilds',
    () async {
      final g = newGame();
      final bot = Bot(g);
      for (var i = 0; i < 10; i++) {
        bot.week();
      }
      await saveAndProve(g);
      // Pretend the file was written by the previous data version.
      final raw = sqlite3.open(path)
        ..execute("UPDATE meta SET value = ? WHERE key = 'version'", [
          '${SaveCodec.currentVersion - 1}',
        ])
        ..close();
      expect(raw, isNotNull);
      final real = SaveCodec.migrations[SaveCodec.currentVersion - 1];
      SaveCodec.migrations[SaveCodec.currentVersion - 1] = (data) {
        final world = Map<String, Object?>.of(
          data['world']! as Map<String, Object?>,
        );
        world['listings'] = <Object?>[];
        world['offers'] = <Object?>[];
        return {...data, 'world': world};
      };
      try {
        final store = SqliteGameStore(path);
        final r = await store.open() as Opened;
        expect(r.migratedFrom, SaveCodec.currentVersion - 1);
        expect(r.state.world.listings, isEmpty);
        expect(backups('v${SaveCodec.currentVersion - 1}'), hasLength(1));
        await store.close();
        // The rows the step removed are gone from disk, and the order holds.
        final again = await reopen();
        expect(again.world.listings, isEmpty);
        expect(snap(again), snap(r.state));
      } finally {
        // the real step put back (removed, no later test ran it)
        if (real == null) {
          SaveCodec.migrations.remove(SaveCodec.currentVersion - 1);
        } else {
          SaveCodec.migrations[SaveCodec.currentVersion - 1] = real;
        }
      }
    },
  );

  test(
    'a v1 save on disk opens, is upgraded row by row, and plays on',
    () async {
      // the v1 JSON fixture written into the file the way the store lays it out
      final store0 = SqliteGameStore(path);
      await store0.startOver();
      await store0.save(newGame().state);
      await store0.close();
      final v1 =
          (jsonDecode(
                File('../marah_data/test/fixtures/save_v1.json')
                    .readAsStringSync(),
              ) as Map<String, Object?>)['data']!
              as Map<String, Object?>;
      final db = sqlite3.open(path)
        ..execute('DELETE FROM doc')
        ..execute('DELETE FROM camel')
        ..execute('DELETE FROM meta');
      final world = Map<String, Object?>.of(
        v1['world']! as Map<String, Object?>,
      );
      final state = Map<String, Object?>.of(v1)
        ..remove('world')
        ..remove('players')
        ..remove('inboxes');
      var seq = 1;
      for (final k in ['owners', 'listings', 'offers', 'studs', 'festivals']) {
        for (final d in world.remove(k)! as List<Object?>) {
          db.execute('INSERT INTO doc VALUES (?,?,?,?)', [
            k.substring(0, k.length - 1),
            (d! as Map<String, Object?>)['id'],
            seq++,
            jsonEncode(d),
          ]);
        }
      }
      for (final c in world.remove('camels')! as List<Object?>) {
        final m = c! as Map<String, Object?>;
        db.execute('INSERT INTO camel VALUES (?,?,?,?,?)', [
          m['id'],
          seq++,
          m['owner'],
          CamelStatus.values.byName(m['status']! as String).index,
          jsonEncode(m),
        ]);
      }
      for (final p in v1['players']! as List<Object?>) {
        db.execute('INSERT INTO doc VALUES (?,?,?,?)', [
          'player',
          (p! as Map<String, Object?>)['id'],
          seq++,
          jsonEncode(p),
        ]);
      }
      for (final e in (v1['inboxes']! as Map<String, Object?>).entries) {
        db.execute('INSERT INTO doc VALUES (?,?,?,?)', [
          'inbox',
          e.key,
          seq++,
          jsonEncode(e.value),
        ]);
      }
      db
        ..execute(
          "INSERT INTO meta VALUES ('format','marah-db'),('version','1'),"
          "('state',?),('world',?)",
          [jsonEncode(state), jsonEncode(world)],
        )
        ..close();

      final store = SqliteGameStore(path);
      final r = await store.open() as Opened;
      expect(r.migratedFrom, 1);
      expect(checkInvariants(r.state), isEmpty);
      final rows = sqlite3.open(path, mode: OpenMode.readOnly);
      final left = rows
          .select(
            'SELECT count(*) n FROM (SELECT data FROM camel UNION ALL '
            'SELECT data FROM doc UNION ALL SELECT value AS data FROM meta) '
            """WHERE data LIKE '%maghateer%' OR data LIKE '%"mature"%'""",
          )
          .first['n'];
      final version = rows
          .select("SELECT value FROM meta WHERE key = 'version'")
          .first['value'];
      rows.close();
      expect(left, 0);
      expect(version, '${SaveCodec.currentVersion}');
      final g = Game(r.state)..advanceDays(30);
      expect(checkInvariants(g.state), isEmpty);
      await store.save(g.state);
      await store.close();
      expect(snap(await reopen()), snap(g.state));
    },
  );

  test('never replaces a file it has not opened', () async {
    final g = newGame();
    final store = SqliteGameStore(path);
    await store.startOver();
    await store.save(g.state);
    await store.close();
    final careless = SqliteGameStore(path);
    await expectLater(careless.save(newGame(99).state), throwsStateError);
    expect(snap(await reopen()), snap(g.state));
  });

  group('10,000 head', () {
    late Game big;
    setUpAll(() {
      big = newGame(11);
      big.me.farm
        ..capacity = 10010
        ..shepherds = 400
        ..storeKg = 1 << 30
        ..tankL = 1 << 30
        ..barleyKg = 1e8
        ..alfalfaKg = 1e8
        ..waterL = 1e9;
      final sim = Sim(big.state);
      final gen = WorldGen(sim);
      for (var i = 0; i < 9997; i++) {
        gen
                .makeCamel(sim.rng(['bulk', i]), owner: big.me.id, mean: 55)
                .lastPlayerOwner =
            big.me.id;
      }
    });

    test('full save, command save, day save and reopen stay light', () async {
      // timed in real time on a shared machine: tried up to three times, so
      // another process's spike does not fail it; a store grown slow fails
      // every one
      for (var attempt = 1; ; attempt++) {
        final store = SqliteGameStore(path);
        await store.startOver();
        final w = Stopwatch()..start();
        await store.save(big.state);
        final full = w.elapsedMilliseconds;

        final c = GameView(big.state, big.me.id).herd.first;
        big.dispatch(RenameCamel(big.me.id, c.id, 'الغالية $attempt'));
        w.reset();
        await store.save(big.state);
        final command = w.elapsedMicroseconds / 1000;

        big.advanceDays(1); // every camel's condition moves
        w.reset();
        await store.save(big.state);
        final day = w.elapsedMilliseconds;
        final dayRows = store.lastWrite.camels;
        await store.close();

        w.reset();
        final reopened = await reopen();
        final open = w.elapsedMilliseconds;
        final size = File(path).lengthSync() ~/ 1024;

        // Generous limits for shared CI machines; measured values in the
        // printout.
        // ignore: avoid_print
        print(
          '10k head: full save $full ms, command save '
          '${command.toStringAsFixed(1)} ms, day save $day ms ($dayRows rows), '
          'reopen $open ms, file $size KB',
        );
        expect(snap(reopened), snap(big.state));
        final light = command < 50 && full < 5000 && day < 3000 && open < 5000;
        if (light || attempt == 3) {
          expect(command, lessThan(50));
          expect(full, lessThan(5000));
          expect(day, lessThan(3000));
          expect(open, lessThan(5000));
          break;
        }
      }
    });
  });
}
