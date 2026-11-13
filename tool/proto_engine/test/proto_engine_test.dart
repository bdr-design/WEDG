// Runs on the Dart VM and in node (`dart test -p vm,node`): the prototype's
// worker runs this code compiled to JavaScript.
import 'dart:async';
import 'dart:convert';

import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_proto_engine/commands_json.dart';
import 'package:marah_proto_engine/same_seed.dart';
import 'package:marah_proto_engine/worker_backend.dart';
import 'package:marah_runtime/marah_runtime.dart';
import 'package:test/test.dart';

const me = OwnerId('p1');

const params = NewGameParams(
  seed: 11,
  playerName: 'اللاعب',
  farmName: 'العزبة',
  region: Region.qassim,
  favourite: ColorCategory.wodh,
);

DateTime fixedNow() => DateTime.utc(2026, 11, 12, 9);

void main() {
  group('commands from JSON', () {
    // One of every command (commandToJson's switch is exhaustive over the
    // sealed Command, so a new one cannot be missing from here unnoticed for
    // long: add it to this list when the compiler asks for it there).
    final every = <Map<String, Object?>>[
      {'type': 'orderSupply', 'supply': 'water', 'units': 2, 'tanker': 'small'},
      {'type': 'orderSupply', 'supply': 'barley', 'units': 3},
      {'type': 'setFeedPlan', 'plan': 'premium'},
      {'type': 'buyListing', 'listing': 'l1'},
      {'type': 'bargain', 'listing': 'l1', 'amount': 41000},
      {'type': 'listForSale', 'camel': 'c1', 'askPrice': 52000},
      {'type': 'cancelListing', 'listing': 'l2'},
      {'type': 'acceptOffer', 'offer': 'o1'},
      {'type': 'declineOffer', 'offer': 'o2'},
      {'type': 'quickSale', 'camel': 'c2'},
      {'type': 'mateWithOwnBull', 'female': 'c3', 'bull': 'c4'},
      {'type': 'mateWithStud', 'female': 'c3', 'stud': 's1'},
      {'type': 'treat', 'camel': 'c5'},
      {'type': 'renameCamel', 'camel': 'c5', 'name': 'الشعلة'},
      {'type': 'setShepherds', 'count': 3},
      {'type': 'buildFacility', 'facility': 'tank'},
      {'type': 'setCalfShare', 'share': 'quarter'},
      {
        'type': 'enterRound',
        'festival': 'f1',
        'round': 'r1',
        'camels': ['c6'],
      },
      {
        'type': 'enterRound',
        'festival': 'f1',
        'round': 'r2',
        'camels': ['c7', 'c8', 'c9'],
      },
      {'type': 'withdrawEntry', 'festival': 'f1', 'round': 'r1', 'camel': 'c6'},
      {'type': 'tamper', 'camel': 'c6', 'kind': 'botox', 'strength': 2},
    ];

    test('every command reads and writes back the same', () {
      for (final j in every) {
        final c = commandFromJson(me, j);
        expect(c, isNotNull, reason: '$j');
        expect(c!.actor, me);
        expect(commandToJson(c), j);
      }
      final types = {for (final j in every) j['type']};
      expect(types, hasLength(19)); // every kind of command
    });

    test('the actor is always the player, whatever the JSON says', () {
      final c = commandFromJson(me, {
        'type': 'treat',
        'camel': 'c1',
        'actor': 'p9',
      });
      expect(c!.actor, me);
    });

    test('unknown or malformed commands are null, not a throw', () {
      for (final j in <Map<String, Object?>>[
        {},
        {'type': 'giveMeMoney'},
        {'type': 'orderSupply', 'supply': 'petrol', 'units': 1},
        {
          'type': 'orderSupply',
          'supply': 'water',
          'units': 1,
          'tanker': 'huge',
        },
        {'type': 'orderSupply', 'supply': 'water'},
        {'type': 'orderSupply', 'supply': 'water', 'units': '2'},
        {'type': 'orderSupply', 'supply': 'water', 'units': 2.5},
        {'type': 'orderSupply', 'supply': 'water', 'units': double.nan},
        {'type': 'setShepherds', 'count': double.infinity},
        {'type': 'listForSale', 'camel': 'c1', 'askPrice': 1e300},
        {'type': 'bargain', 'listing': 'l1', 'amount': 9.007199254740992e15},
        {'type': 'treat', 'camel': 7},
        {'type': 'enterRound', 'festival': 'f1', 'camel': 'c1'},
        {'type': 'enterRound', 'festival': 'f1', 'round': 'r1', 'camels': 'c1'},
        {'type': 'tamper', 'camel': 'c1', 'kind': 'magic', 'strength': 1},
        {'type': 'tamper', 'camel': 'c1', 'kind': 'dye', 'strength': 1.5},
      ]) {
        expect(commandFromJson(me, j), isNull, reason: '$j');
      }
      // a whole number sent as 2.0 (JavaScript cannot tell) is fine
      expect(
        commandFromJson(me, {'type': 'setShepherds', 'count': 2.0}),
        isA<SetShepherds>().having((c) => c.count, 'count', 2),
      );
    });
  });

  group('canonical JSON', () {
    test('numbers are written the same on both platforms', () {
      expect(
        canonicalJson({
          'a': 1.0,
          'b': [1.5, -0.25, 3, null, true, 'x"y\\z\n'],
          'c': {'d': 1e-7, 'e': 2.0e20},
        }),
        r'{"a":1,"b":[1.5,-0.25,3,null,true,"x\"y\\z\u000a"],'
        r'"c":{"d":1e-7,"e":200000000000000000000}}',
      );
      final values = <num>[
        0.0,
        -0.0,
        0.1 + 0.2,
        1 / 3,
        123456789.125,
        -2.5e-5,
        1e21,
        1.5e300,
        5e-324,
        4503599627370497.0,
        9007199254740991,
      ];
      expect(
        canonicalJson(values),
        '[0,-0,0.30000000000000004,0.3333333333333333,123456789.125,'
        '-0.000025,1e+21,1.5e+300,5e-324,4503599627370497,9007199254740991]',
      );
    });

    test('the hash stays inside 30 bits', () {
      final h = textHash('مراح' * 1000);
      expect(h, inInclusiveRange(0, 0x3FFFFFFF));
      expect(textHash(''), 0);
    });
  });

  group('the worker backend', () {
    /// A page that keeps every write in [kept] and answers it a moment later
    /// (or refuses while [refuse] is set).
    WorkerBackend backend(
      Map<String, String> kept, {
      Map<String, String> seed = const {},
      bool Function()? refuse,
      List<int>? seqs,
    }) {
      var n = 0;
      late final PageSaveIo io;
      io = PageSaveIo(seed, (seq, k, v) {
        seqs?.add(seq);
        scheduleMicrotask(() {
          if (refuse?.call() ?? false) {
            return io.stored(seq, ok: false, error: 'disk full');
          }
          v == null ? kept.remove(k) : kept[k] = v;
          io.stored(seq, ok: true);
        });
      }, nextSeq: () => ++n);
      return WorkerBackend(seed, io);
    }

    test('every change goes to the page, numbered, and lands', () async {
      final kept = <String, String>{'a': '1'};
      final seqs = <int>[];
      final b = backend(kept, seed: {'a': '1'}, seqs: seqs);
      expect(await b.read('a'), '1');
      await b.write('b', '2');
      await b.copy('a', 'c');
      await b.copy('missing', 'd');
      await b.delete('a');
      expect(seqs, [1, 2, 3]);
      expect(kept, {'b': '2', 'c': '1'});
      expect(await b.read('a'), isNull);
      expect(await b.read('d'), isNull);
      expect(await b.read('c'), '1');
    });

    test('a write the page refuses, or never answers, fails', () async {
      final b = backend({}, refuse: () => true);
      await expectLater(b.write('k', 'v'), throwsA(isA<SaveWriteFailed>()));

      final silent = PageSaveIo(
        const {},
        (_, _, _) {},
        nextSeq: () => 1,
        timeout: const Duration(milliseconds: 20),
      );
      await expectLater(silent.keep('k', 'v'), throwsA(isA<SaveWriteFailed>()));
      silent.stored(1, ok: true); // a late answer changes nothing
    });

    test(
      'the app server: read, written, refused, or silent and cut off',
      () async {
        final files = <String, String>{'marah.save': 'S'};
        var mode = 'ok';
        final calls = <String>[];
        final stamps = <String>[];
        Future<(int, String)> http(
          String method,
          String url,
          Map<String, String> headers,
          String? body,
          Duration timeout,
        ) async {
          calls.add('$method $url ${headers['x-marah-save']}');
          if (method != 'GET') stamps.add(headers['x-marah-write']!);
          if (mode == 'silent') {
            // never answers: the call must be cut off at the timeout
            return Future<(int, String)>.delayed(const Duration(days: 1))
                .timeout(timeout);
          }
          if (mode == 'refuse') return (500, '');
          if (mode == 'superseded') return (409, '');
          final key = Uri.decodeComponent(url.split('/save/').last);
          if (method == 'GET') return (200, jsonEncode(files));
          method == 'PUT' ? files[key] = body! : files.remove(key);
          return (204, '');
        }

        final io = ServerSaveIo(
          http,
          base: 'http://127.0.0.1:9',
          token: 't0k',
          timeout: const Duration(milliseconds: 30),
        );
        expect(await io.load(), {'marah.save': 'S'});
        await io.keep('marah.save.prev', 'P');
        await io.keep('marah.save', null);
        expect(files, {'marah.save.prev': 'P'});
        expect(calls.first, 'GET http://127.0.0.1:9/save t0k');
        expect(calls.last, 'DELETE http://127.0.0.1:9/save/marah.save t0k');
        // each write numbered in order under this engine's mark
        expect(stamps, ['${io.loadId}:1', '${io.loadId}:2']);
        expect(
          ServerSaveIo(http, base: '', token: '').loadId,
          isNot(io.loadId),
        );
        mode = 'superseded';
        await expectLater(io.keep('k', 'v'), throwsA(isA<SaveWriteFailed>()));
        mode = 'refuse';
        await expectLater(io.keep('k', 'v'), throwsA(isA<SaveWriteFailed>()));
        await expectLater(io.load(), throwsA(isA<SaveWriteFailed>()));
        mode = 'silent';
        final sw = Stopwatch()..start();
        await expectLater(io.keep('k', 'v'), throwsA(isA<SaveWriteFailed>()));
        expect(sw.elapsedMilliseconds, lessThan(2000));
      },
    );

    test(
      'a write the page refuses reaches the engine, which tries again',
      () async {
        var refuse = false;
        final kept = <String, String>{};
        final pushes = <Push>[];
        final e = EngineCore(
          store: SaveStore(backend(kept, refuse: () => refuse)),
          emit: pushes.add,
          now: fixedNow,
        );
        await e.open();
        await e.newGame(params);
        refuse = true;
        await e.dispatch(OrderSupply(e.game!.me.id, Supply.barley, 1));
        expect(
          pushes.whereType<SaveStatus>().map((p) => p.ok),
          contains(false),
        );
        refuse = false;
        await e.flush();
        expect(pushes.whereType<SaveStatus>().last.ok, isTrue);
        expect(kept['marah.save'], contains('"units":1'));
        await e.close();
      },
    );

    test(
      'a game saved through the page opens again from what it kept',
      () async {
        final page = <String, String>{};
        final first = EngineCore(
          store: SaveStore(backend(page)),
          emit: (_) {},
          now: fixedNow,
        );
        expect(await first.open(), isA<NoGame>());
        await first.newGame(params);
        final r = await first.dispatch(
          commandFromJson(first.game!.me.id, {
            'type': 'orderSupply',
            'supply': 'water',
            'units': 1,
            'tanker': 'small',
          })!,
        );
        expect(r.ok, isTrue, reason: r is Err ? '${r.error.code}' : '');
        await first.flush();
        final saved = stateLine(first.game!.state);
        await first.close();
        expect(page, contains('marah.save'));
        expect(page, contains('marah.save.prev'));

        final second = EngineCore(
          store: SaveStore(backend(page, seed: page)),
          emit: (_) {},
          now: fixedNow,
        );
        expect(await second.open(), isA<GameOpened>());
        expect(stateLine(second.game!.state), saved);
        await second.close();
      },
    );
  });

  group('the snapshot as JSON', () {
    test('is plain JSON and carries the stores', () async {
      final pushes = <Push>[];
      final e = EngineCore(
        store: SaveStore(MemoryBackend()),
        emit: pushes.add,
        now: fixedNow,
      );
      await e.open();
      await e.newGame(params);
      await e.dispatch(OrderSupply(e.game!.me.id, Supply.barley, 3));
      final snap = pushes.whereType<SnapshotPush>().last.snapshot;
      await e.close();

      final j = jsonDecode(
        jsonEncode(SnapshotJson.snapshot(snap)),
      ) as Map<String, Object?>;
      expect(j['playerName'], 'اللاعب');
      expect(j['date'], matches(RegExp(r'^\d{4}-\d\d-\d\d$')));
      expect(j['cash'], snap.cash);
      final farm = j['farm']! as Map<String, Object?>;
      expect(farm['region'], 'qassim');
      final supplies = (farm['supplies']! as List).cast<Map<String, Object?>>();
      expect(supplies.map((s) => s['supply']), ['barley', 'alfalfa', 'water']);
      final barley = supplies.first;
      expect(barley['onTheWay'], 3);
      expect(barley['unitSize'], Provisions.unitSize(Supply.barley));
      expect(barley['short'], isFalse);
      final herd = j['herd']! as Map<String, Object?>;
      expect(herd['total'], snap.herd.total);
      expect((j['herdTop']! as List).length, snap.herdTop.length);
      // the cards carry what the screens show, and only that (CamelCard's
      // fields: a new one is a choice to look at, not a leak by default)
      final card = (j['herdTop']! as List).first as Map<String, Object?>;
      expect(card.keys.toSet(), {
        'id', 'name', 'sex', 'category', 'ageClass', 'ageDays', 'quality', //
        'estimateLow', 'estimateHigh', 'condition', 'health', 'illness',
        'pregnant', 'dueOn', 'awaitingCheck', 'listed', 'entered', 'bestRank',
        'crossbred',
        // the age's name as the camel's sex has it (ageClass and sex, read)
        'ageName',
        // الحراج: bought today and on the truck, and the broker's price for
        // one's own camel (his own eye: not the value read back)
        'onTheWay', 'quickSale',
      });
      expect(card['onTheWay'], isFalse);
      expect(card['quickSale'], isA<int>());
      // the 3D farm's camels (the start's camel and her calf), and the milk
      // to a tenth of a litre
      expect((j['yard']! as List).length, 2);
      // the start's calf, eight and a half months and still suckling, is a
      // حوار though its age class is مخلول (the owner, 13 Nov 2026)
      final calf = (j['yard']! as List).cast<Map<String, Object?>>().firstWhere(
        (c) => c['ageDays']! as int < 365,
      );
      expect(calf['ageClass'], 'makhlool');
      expect(calf['ageName'], anyOf('حوار', 'حوارة'));
      final milk = farm['milk']! as Map<String, Object?>;
      expect(milk['nursing'], 1);
      final litres = milk['litres']! as num;
      expect((litres * 10).round() / 10, litres);
    });

    test('the stores as the game holds them', () async {
      final pushes = <Push>[];
      final e = EngineCore(
        store: SaveStore(MemoryBackend()),
        emit: pushes.add,
        now: fixedNow,
      );
      await e.open();
      await e.newGame(params);
      final me = e.game!.me.id;
      await e.dispatch(OrderSupply(me, Supply.alfalfa, 2));
      await e.dispatch(SetFeedPlan(me, FeedPlan.premium));
      final snap = pushes.whereType<SnapshotPush>().last.snapshot;
      final v = GameView(e.game!.state, me);
      final farm = e.game!.me.farm;
      await e.close();

      final f =
          (jsonDecode(jsonEncode(SnapshotJson.snapshot(snap)))
                  as Map<String, Object?>)['farm']!
              as Map<String, Object?>;
      expect(f['storeKg'], farm.storeKg);
      expect(f['tankL'], farm.tankL);
      expect(f['dryDays'], farm.dryDays);
      expect(f['feedPlan'], 'premium');
      final root = jsonDecode(
        jsonEncode(SnapshotJson.snapshot(snap)),
      ) as Map<String, Object?>;
      expect(root['todayNet'], v.todayNet.value);
      final rations = (f['rations']! as List).cast<Map<String, Object?>>();
      expect(rations.map((r) => r['plan']), ['economy', 'standard', 'premium']);
      for (final r in rations) {
        final plan = FeedPlan.values.byName(r['plan']! as String);
        expect(r['costPerDay'], v.dailyFeedFor(plan).value);
        expect(r['conditionTarget'], plan.conditionTarget);
      }
      expect(f['pastureGreen'], v.pastureGreen);
      expect(f['thirstDays'], v.thirstDays);
      final tankers = (f['tankers']! as List).cast<Map<String, Object?>>();
      expect(tankers.map((t) => t['tanker']), ['large', 'small']);
      expect(tankers.map((t) => t['litres']), [19000, 6000]);
      expect(tankers.map((t) => t['price']), [200, 120]);
      expect(tankers.first['room'], v.roomFor(Supply.water));
      expect(
        tankers.last['room'],
        v.roomFor(Supply.water, tanker: Tanker.small),
      );
      final supplies = (f['supplies']! as List).cast<Map<String, Object?>>();
      for (final (i, s) in Supply.values.indexed) {
        final j = supplies[i];
        expect(j['supply'], s.name);
        expect(j['amount'], v.inStore(s).floor(), reason: s.name);
        expect(j['daysLeft'], v.daysLeft(s), reason: s.name);
        expect(j['room'], v.roomFor(s), reason: s.name);
        expect(j['unitPrice'], v.unitPrice(s).value, reason: s.name);
        expect(j['unitSize'], Provisions.unitSize(s), reason: s.name);
        expect(j['onTheWay'], s == Supply.alfalfa ? 2 : 0, reason: s.name);
        expect(
          j['onTheWayAmount'],
          s == Supply.alfalfa ? 50 : 0,
          reason: s.name,
        );
        final n = v.dailyNeeds;
        expect(
          j['need'],
          closeTo(switch (s) {
            Supply.barley => n.barley,
            Supply.alfalfa => n.alfalfa,
            Supply.water => n.water,
          }, 1e-9),
          reason: s.name,
        );
        expect(j['short'], farm.short.contains(s), reason: s.name);
      }
      // a richer ration empties the stores sooner
      expect(supplies[0]['daysLeft'], lessThan(30));
    });
  });

  test('the same seed gives the same lines (CI compares VM and node)', () {
    final a = sameSeedLines(weeks: 8).toList();
    final b = sameSeedLines(weeks: 8).toList();
    expect(a, hasLength(4)); // weeks 0, 4, 8, and the extras' counts
    expect(a, b);
  });
}
