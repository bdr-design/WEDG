// The worker's protocol (lib/worker_host.dart), on the Dart VM and in node.
import 'dart:async';
import 'dart:convert';

import 'package:marah_proto_engine/worker_host.dart';
import 'package:test/test.dart';

/// The page's side: keeps every write (or refuses while [refuse] is set) and
/// answers it a moment later, as engine.js does.
class Page {
  Page({this.answerAfter = Duration.zero, bool server = false}) {
    host = WorkerHost(
      post: (j) => messages.add(jsonDecode(j) as Map<String, Object?>),
      http: server ? _http : null,
      saveTimeout: const Duration(milliseconds: 200),
      postStore: (seq, k, v) {
        writes.add((seq, k, v));
        Future<void>.delayed(answerAfter, () {
          if (!refuse) v == null ? kept.remove(k) : kept[k] = v;
          host.receive(
            jsonEncode({
              'op': 'stored',
              'seq': seq,
              'ok': !refuse,
              'error': refuse ? 'disk full' : null,
            }),
          );
        });
      },
    );
  }

  late final WorkerHost host;
  final Duration answerAfter;

  /// The app's server, as the worker reaches it: keeps the files in [kept];
  /// while [hang] is set a request never answers (cut off at the timeout).
  bool hang = false;
  Future<(int, String)> _http(
    String method,
    String url,
    Map<String, String> headers,
    String? body,
    Duration timeout,
  ) async {
    if (headers['x-marah-save'] != 'tok') return (403, '');
    if (hang) return Completer<(int, String)>().future.timeout(timeout);
    await Future<void>.delayed(answerAfter);
    if (method == 'GET') return (200, jsonEncode(kept));
    final key = Uri.decodeComponent(url.split('/save/').last);
    writes.add((0, key, body));
    method == 'PUT' ? kept[key] = body! : kept.remove(key);
    return (204, '');
  }

  final kept = <String, String>{};
  final messages = <Map<String, Object?>>[];
  final writes = <(int, String, String?)>[];
  bool refuse = false;
  int _id = 0;

  int send(String op, [Map<String, Object?> extra = const {}]) {
    final id = ++_id;
    host.receive(jsonEncode({'op': op, 'id': id, ...extra}));
    return id;
  }

  Future<Map<String, Object?>> answer(int id) => waitFor(
    (m) => (m['type'] == 'reply' || m['type'] == 'error') && m['id'] == id,
  );

  Future<Map<String, Object?>> call(
    String op, [
    Map<String, Object?> extra = const {},
  ]) => answer(send(op, extra));

  Future<Map<String, Object?>> waitFor(
    bool Function(Map<String, Object?>) pred, {
    Duration within = const Duration(seconds: 20),
  }) async {
    final end = DateTime.now().add(within);
    while (DateTime.now().isBefore(end)) {
      for (final m in messages) {
        if (pred(m)) return m;
      }
      await Future<void>.delayed(const Duration(milliseconds: 2));
    }
    throw TimeoutException('no such message');
  }

  Map<String, Object?>? get lastSnapshot {
    final s = messages.lastWhere(
      (m) => m['type'] == 'snapshot',
      orElse: () => const {},
    );
    return s['snapshot'] as Map<String, Object?>?;
  }

  int get today => lastSnapshot!['today']! as int;
}

const newGame = {'seed': 11, 'region': 'qassim', 'favourite': 'wodh'};

void main() {
  test(
    'starts a new game, saves it through the page, answers in order',
    () async {
      final page = Page();
      final start = page.send('start', {'newGame': newGame});
      // sent before the start is answered: it waits its turn
      final order = page.send('dispatch', {
        'command': {'type': 'orderSupply', 'supply': 'barley', 'units': 2},
      });
      final a = await page.answer(start);
      final b = await page.answer(order);
      expect(a, containsPair('status', 'new'));
      expect(b, containsPair('ok', true));
      expect(page.messages.indexOf(a), lessThan(page.messages.indexOf(b)));
      expect(page.kept.keys, containsAll(['marah.save', 'marah.save.prev']));
      final barley = (page.lastSnapshot!['farm']! as Map)['supplies'] as List;
      expect((barley.first as Map)['onTheWay'], 2);
      await page.call('pause');
    },
  );

  test('refuses what it cannot read, and says so with the id', () async {
    final page = Page();
    expect(await page.call('flush'), containsPair('error', 'noEngine'));
    expect(await page.call('dispatch'), containsPair('error', 'noEngine'));
    page.host.receive('{not json');
    page.host.receive('[1, 2]');
    page.host.receive(null);
    expect(
      page.messages.where((m) => m['error'] == 'badMessage'),
      hasLength(3),
    );
    expect(
      await page.call('start', {
        'newGame': {...newGame, 'region': 'mars'},
      }),
      containsPair('error', 'badNewGame'),
    );
    expect(
      await page.call('start', {
        'newGame': {...newGame, 'seed': 1.5},
      }),
      containsPair('error', 'badNewGame'),
    );
    for (final scale in [0, -1, 2e6, 'fast']) {
      expect(
        await page.call('start', {'newGame': newGame, 'timeScale': scale}),
        containsPair('error', 'badTimeScale'),
      );
    }
    expect(page.writes, isEmpty); // nothing started
    await page.call('start', {'newGame': newGame});
    expect(await page.call('dispatch'), containsPair('error', 'badCommand'));
    expect(
      await page.call('dispatch', {'command': 'treat'}),
      containsPair('error', 'badCommand'),
    );
    expect(await page.call('fly'), containsPair('error', 'unknownOp'));
    // a bad second start leaves the running engine as it was
    expect(
      await page.call('start', {'timeScale': 0}),
      containsPair('error', 'badTimeScale'),
    );
    expect(
      await page.call('dispatch', {
        'command': {'type': 'setShepherds', 'count': 1},
      }),
      containsPair('ok', true),
    );
    await page.call('pause');
  });

  test('a second start stops the first engine before the next opens', () async {
    final page = Page();
    // the first runs a fast clock, so it would write again within milliseconds
    await page.call('start', {'newGame': newGame, 'timeScale': 1e6});
    await page.waitFor(
      (m) =>
          m['type'] == 'snapshot' &&
          (m['snapshot']! as Map)['today'] as int > 275,
    );
    final again = await page.call('start', {
      'store': {...page.kept},
    });
    expect(again, containsPair('status', 'opened'));
    final r = await page.call('dispatch', {
      'command': {'type': 'orderSupply', 'supply': 'barley', 'units': 5},
    });
    expect(r, containsPair('ok', true));
    await page.call('pause');
    final after = page.writes.length;
    final saved = page.kept['marah.save'];
    await Future<void>.delayed(const Duration(milliseconds: 300));
    expect(page.writes.length, after, reason: 'nothing writes after the pause');
    expect(page.kept['marah.save'], saved);
    expect(saved, contains('"units":5'));
  });

  test('a faster clock moves the world on its own', () async {
    final page = Page();
    await page.call('start', {'newGame': newGame, 'timeScale': 1e6});
    final d0 = page.today;
    await Future<void>.delayed(const Duration(milliseconds: 400));
    expect(page.today, greaterThan(d0 + 5));
    await page.call('pause');
    final d1 = page.today;
    await Future<void>.delayed(const Duration(milliseconds: 200));
    expect(page.today, d1, reason: 'paused, the world waits');
  });

  test('a write the page refuses is reported and tried again', () async {
    final page = Page();
    await page.call('start', {'newGame': newGame});
    page.refuse = true;
    await page.call('dispatch', {
      'command': {'type': 'orderSupply', 'supply': 'water', 'units': 1},
    });
    await page.waitFor((m) => m['type'] == 'save' && m['ok'] == false);
    page.refuse = false;
    await page.call('flush');
    await page.waitFor((m) => m['type'] == 'save' && m['ok'] == true);
    expect(page.kept['marah.save'], contains('"supply":"water"'));
    await page.call('pause');
  });

  test(
    'a broken save: opened as failed, then the last good one or a new game',
    () async {
      final page = Page();
      await page.call('start', {'newGame': newGame});
      await page.call('pause');
      final good = {...page.kept};
      final broken = Page();
      final r = await broken.call('start', {
        'store': {...good, 'marah.save': '{"broken'},
      });
      expect(r['ok'], isFalse);
      expect(r['status'], startsWith('failed'));
      expect(broken.kept['marah.save.broken'], '{"broken');
      expect(
        await broken.call('openPrevious'),
        containsPair('status', 'opened'),
      );
      expect(broken.lastSnapshot, isNotNull);
      expect(
        await broken.call('startOver', {
          'newGame': {...newGame, 'seed': 12},
        }),
        containsPair('status', 'new'),
      );
      await broken.call('pause');
    },
  );

  test('the app server: the worker keeps the save itself', () async {
    final page = Page(server: true);
    const server = {'base': 'http://127.0.0.1:9', 'token': 'tok'};
    final r = await page.call('start', {'server': server, 'newGame': newGame});
    expect(r, containsPair('status', 'new'));
    expect(page.kept.keys, containsAll(['marah.save', 'marah.save.prev']));
    expect(
      page.messages.where((m) => m['type'] == 'wrote' && m['ok'] == true),
      isNotEmpty,
    );
    await page.call('dispatch', {
      'command': {'type': 'orderSupply', 'supply': 'water', 'units': 1},
    });
    await page.call('pause');
    // opened again from the server's files
    final again = Page(server: true)..kept.addAll(page.kept);
    expect(
      await again.call('start', {'server': server}),
      containsPair('status', 'opened'),
    );
    await again.call('pause');
    // without a way to reach it, or with a bad key, nothing starts
    expect(
      await Page().call('start', {'server': server}),
      containsPair('error', 'badServer'),
    );
    expect(
      await Page(server: true).call('start', {
        'server': {...server, 'token': 'nope'},
      }),
      containsPair('error', 'saveUnreadable'),
    );
  });

  test(
    'a request that never answers is cut off; later commands go on',
    () async {
      final page = Page(server: true);
      await page.call('start', {
        'server': {'base': 'http://127.0.0.1:9', 'token': 'tok'},
        'newGame': newGame,
      });
      page.hang = true;
      final sw = Stopwatch()..start();
      await page.call('dispatch', {
        'command': {'type': 'orderSupply', 'supply': 'barley', 'units': 1},
      });
      expect(sw.elapsedMilliseconds, lessThan(1500));
      await page.waitFor((m) => m['type'] == 'save' && m['ok'] == false);
      page.hang = false;
      sw.reset();
      final r = await page.call('dispatch', {
        'command': {'type': 'orderSupply', 'supply': 'barley', 'units': 1},
      });
      expect(r, containsPair('ok', true));
      expect(sw.elapsedMilliseconds, lessThan(1500));
      await page.call('flush');
      await page.waitFor((m) => m['type'] == 'save' && m['ok'] == true);
      await page.call('pause');
    },
  );

  test('a fast clock never queues its ticks behind slow saves', () async {
    // each write answered after 20 ms, a game day every 12 ms
    final page = Page(answerAfter: const Duration(milliseconds: 20));
    await page.call('start', {'newGame': newGame, 'timeScale': 1e6});
    await Future<void>.delayed(const Duration(seconds: 2));
    final sw = Stopwatch()..start();
    await page.call('dispatch', {
      'command': {'type': 'setShepherds', 'count': 1},
    });
    expect(
      sw.elapsedMilliseconds,
      lessThan(600),
      reason: 'waited behind ticks',
    );
    sw.reset();
    await page.call('pause');
    expect(sw.elapsedMilliseconds, lessThan(600));
  });

  test('startOver with bad settings is refused, not thrown', () async {
    final page = Page();
    await page.call('start', {'newGame': newGame});
    expect(
      await page.call('startOver', {
        'newGame': {'region': 'mars'},
      }),
      containsPair('error', 'badNewGame'),
    );
    await page.call('pause');
  });
}
