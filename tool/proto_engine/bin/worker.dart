// The rules engine in the 3D design prototype's Web Worker (docs/plan-gameplay.md, G2): the game app's own engine
// (marah_runtime's EngineCore: the clock's catch-up, commands in order, saving, the screens' view models), compiled
// to JavaScript. The page talks to it in JSON strings:
//   page -> worker: {op: 'start', id, store: {key: text}, newGame: {...}, timeScale?}
//                   {op: 'dispatch', id, command: {type, ...}} | {op: 'flush' | 'pause' | 'resume', id}
//   worker -> page: {type: 'ready'} | {type: 'reply', id, ...} | {type: 'snapshot', snapshot}
//                   {type: 'store', key, value} (the page keeps it) | {type: 'save', ok, error}
//                   {type: 'catchUp', done, total} | {type: 'notice', kind, ...} | {type: 'error', id, error}
import 'dart:async';
import 'dart:convert';
import 'dart:js_interop';

import 'package:marah_data/marah_data.dart';
import 'package:marah_domain/marah_domain.dart';
import 'package:marah_proto_engine/commands_json.dart';
import 'package:marah_proto_engine/worker_backend.dart';
import 'package:marah_runtime/marah_runtime.dart';

@JS('self')
external _Scope get _self;

extension type _Scope._(JSObject _) implements JSObject {
  external set onmessage(JSFunction f);
  external void postMessage(JSAny? message);
}

extension type _Message._(JSObject _) implements JSObject {
  external JSAny? get data;
}

void _post(Map<String, Object?> m) => _self.postMessage(jsonEncode(m).toJS);
void _reply(Object? id, Map<String, Object?> m) =>
    _post({'type': 'reply', 'id': id, ...m});

EngineCore? _core;

void main() {
  _self.onmessage = ((_Message e) {
    final m = jsonDecode((e.data! as JSString).toDart) as Map<String, Object?>;
    unawaited(_handle(m));
  }).toJS;
  _post({'type': 'ready'});
}

Future<void> _handle(Map<String, Object?> m) async {
  final id = m['id'];
  try {
    switch (m['op']) {
      case 'start':
        final seed = <String, String>{
          for (final e in ((m['store'] as Map?) ?? const {}).entries)
            e.key as String: e.value as String,
        };
        final store = SaveStore(
          WorkerBackend(
            seed,
            (k, v) => _post({'type': 'store', 'key': k, 'value': v}),
          ),
        );
        // a faster clock for trying things (the game's own is a real day for a
        // game week, approved by the owner)
        final scale = (m['timeScale'] as num?)?.toDouble() ?? 1;
        final t0 = DateTime.now();
        DateTime now() => scale == 1
            ? DateTime.now()
            : t0.add(DateTime.now().difference(t0) * scale);
        _core = EngineCore(store: store, emit: _push, now: now);
        final status = await _core!.open();
        var opened = switch (status) {
          GameOpened() => 'opened',
          NoGame() => 'new',
          GameOpenFailed(:final problem, :final detail) =>
            'failed ${problem.name}: $detail',
        };
        if (status is NoGame) {
          final p = (m['newGame'] as Map?) ?? const {};
          await _core!.newGame(
            NewGameParams(
              seed:
                  (p['seed'] as num?)?.toInt() ?? now().millisecondsSinceEpoch,
              playerName: (p['playerName'] as String?) ?? 'اللاعب',
              farmName: (p['farmName'] as String?) ?? 'العزبة',
              region: Region.values.byName(
                (p['region'] as String?) ?? 'qassim',
              ),
              favourite: ColorCategory.values.byName(
                (p['favourite'] as String?) ?? 'wodh',
              ),
            ),
          );
          opened = 'new';
        }
        _reply(id, {'status': opened});
      case 'dispatch':
        final game = _core?.game;
        if (game == null) return _reply(id, {'ok': false, 'error': 'noGame'});
        final cmd = commandFromJson(
          game.me.id,
          (m['command']! as Map).cast<String, Object?>(),
        );
        if (cmd == null)
          return _reply(id, {'ok': false, 'error': 'badCommand'});
        final r = await _core!.dispatch(cmd);
        _reply(id, {
          'ok': r.ok,
          'error': r is Err
              ? {'code': r.error.code.name, 'params': r.error.params}
              : null,
          'events': [for (final e in r.events) e.toJson()],
        });
      case 'flush':
        await _core?.flush();
        _reply(id, {});
      case 'pause':
        await _core?.pause();
        _reply(id, {});
      case 'resume':
        await _core?.resume();
        _reply(id, {});
      default:
        _post({'type': 'error', 'id': id, 'error': 'unknown op ${m['op']}'});
    }
  } on Object catch (e) {
    _post({'type': 'error', 'id': id, 'error': '$e'});
  }
}

void _push(Push p) => switch (p) {
  SnapshotPush(:final snapshot) => _post({
    'type': 'snapshot',
    'snapshot': SnapshotJson.snapshot(snapshot),
  }),
  SaveStatus(:final ok, :final error) => _post({
    'type': 'save',
    'ok': ok,
    'error': error,
  }),
  CatchUpProgress(:final done, :final total) => _post({
    'type': 'catchUp',
    'done': done,
    'total': total,
  }),
  CatchUpCapped(:final skippedDays) => _post({
    'type': 'notice',
    'kind': 'catchUpCapped',
    'skippedDays': skippedDays,
  }),
  StateRecovered(:final reason) => _post({
    'type': 'notice',
    'kind': 'recovered',
    'reason': reason,
  }),
  BackupWarning() => _post({'type': 'notice', 'kind': 'backup'}),
  EngineHalted(:final reason) => _post({
    'type': 'notice',
    'kind': 'halted',
    'reason': reason,
  }),
  EngineDown(:final reason) => _post({
    'type': 'notice',
    'kind': 'down',
    'reason': reason,
  }),
};
