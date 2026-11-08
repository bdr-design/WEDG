import 'dart:convert';
import 'dart:io';

import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_domain/src/sim.dart';
import 'package:marah_domain/src/world_gen.dart';
import 'package:marah_domain/testing.dart';
import 'package:marah_store/marah_store.dart';
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

  test('a garbage file is backed up, locked and never replaced', () async {
    File(path).writeAsStringSync('this is not a database');
    final store = SqliteGameStore(path);
    expect(await store.open(), isA<OpenFailed>());
    expect(store.locked, isTrue);
    expect(File('$path.broken').readAsStringSync(), 'this is not a database');
    await store.save(newGame().state);
    expect(File(path).readAsStringSync(), 'this is not a database');
  });

  test('a good open leaves a readable fallback that can be restored', () async {
    final g = newGame();
    final store = SqliteGameStore(path);
    await store.startOver();
    await store.save(g.state);
    await store.close();
    final again = SqliteGameStore(path);
    expect(await again.open(), isA<Opened>());
    await again.close();
    expect(File('$path.prev').existsSync(), isTrue);

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
        ..shepherds = 400;
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
      final store = SqliteGameStore(path);
      await store.startOver();
      final w = Stopwatch()..start();
      await store.save(big.state);
      final full = w.elapsedMilliseconds;

      final c = GameView(big.state, big.me.id).herd.first;
      big.dispatch(RenameCamel(big.me.id, c.id, 'الغالية'));
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
      expect(command, lessThan(50));
      expect(full, lessThan(5000));
      expect(day, lessThan(3000));
      expect(open, lessThan(5000));
      expect(reopened.world.camels.length, big.state.world.camels.length);
    });
  });
}
