// Runs on the Dart VM and in node (`dart test -p vm,node`): the prototype's
// worker runs this code compiled to JavaScript.
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
      {'type': 'orderSupply', 'supply': 'water', 'units': 2},
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
      {'type': 'expandFarm'},
      {'type': 'enterRound', 'festival': 'f1', 'round': 'r1', 'camel': 'c6'},
      {'type': 'withdrawEntry', 'festival': 'f1', 'round': 'r1', 'camel': 'c6'},
    ];

    test('every command reads and writes back the same', () {
      for (final j in every) {
        final c = commandFromJson(me, j);
        expect(c, isNotNull, reason: '$j');
        expect(c!.actor, me);
        expect(commandToJson(c), j);
      }
      final types = {for (final j in every) j['type']};
      expect(types, hasLength(every.length));
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
        {'type': 'orderSupply', 'supply': 'water'},
        {'type': 'orderSupply', 'supply': 'water', 'units': '2'},
        {'type': 'orderSupply', 'supply': 'water', 'units': 2.5},
        {'type': 'orderSupply', 'supply': 'water', 'units': double.nan},
        {'type': 'setShepherds', 'count': double.infinity},
        {'type': 'treat', 'camel': 7},
        {'type': 'enterRound', 'festival': 'f1', 'camel': 'c1'},
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
    test(
      'every change goes to the page; a missing copy does nothing',
      () async {
        final seen = <(String, String?)>[];
        final b = WorkerBackend({'a': '1'}, (k, v) => seen.add((k, v)));
        expect(await b.read('a'), '1');
        await b.write('b', '2');
        await b.copy('a', 'c');
        await b.copy('missing', 'd');
        await b.delete('a');
        expect(seen, [('b', '2'), ('c', '1'), ('a', null)]);
        expect(await b.read('a'), isNull);
        expect(await b.read('d'), isNull);
        expect(await b.read('c'), '1');
      },
    );

    test(
      'a game saved through the page opens again from what it kept',
      () async {
        final page = <String, String>{};
        void keep(String k, String? v) =>
            v == null ? page.remove(k) : page[k] = v;

        final pushes = <Push>[];
        final first = EngineCore(
          store: SaveStore(WorkerBackend(const {}, keep)),
          emit: pushes.add,
          now: fixedNow,
        );
        expect(await first.open(), isA<NoGame>());
        await first.newGame(params);
        final r = await first.dispatch(
          commandFromJson(first.game!.me.id, {
            'type': 'orderSupply',
            'supply': 'water',
            'units': 1,
          })!,
        );
        expect(r.ok, isTrue, reason: r is Err ? '${r.error.code}' : '');
        await first.flush();
        final saved = stateLine(first.game!.state);
        await first.close();
        expect(page, contains('marah.save'));

        final second = EngineCore(
          store: SaveStore(WorkerBackend(page, keep)),
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
      // the cards carry what the screens show and nothing hidden
      final card = (j['herdTop']! as List).first as Map<String, Object?>;
      expect(card.keys, isNot(contains('genes')));
      expect(card.keys, isNot(contains('env')));
    });
  });

  test('the same seed gives the same lines (CI compares VM and node)', () {
    final a = sameSeedLines(weeks: 8).toList();
    final b = sameSeedLines(weeks: 8).toList();
    expect(a, hasLength(3));
    expect(a, b);
  });
}
